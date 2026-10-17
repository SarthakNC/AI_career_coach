import io
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

import pymupdf
import pytesseract
from PIL import Image
from fastapi import HTTPException, status

from config import get_settings

logger = logging.getLogger(__name__)


class PDFValidationError(HTTPException):
    """Raised when a PDF fails security or structural validation."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class OCREngineUnavailableError(HTTPException):
    """Raised when OCR is strictly required to extract text but Tesseract is not configured."""
    def __init__(self, detail: str = "Tesseract OCR engine is not available on this server to process scanned PDF pages."):
        super().__init__(status_code=422, detail=detail)


def get_tesseract_command_path() -> Optional[str]:
    """
    Resolves the executable path to Tesseract OCR.
    Checks environment config, PATH, and standard Windows install paths.
    """
    settings = get_settings()

    # 1. Configured path via environment variable
    if settings.ocr_tesseract_cmd and os.path.exists(settings.ocr_tesseract_cmd):
        return settings.ocr_tesseract_cmd

    # 2. Check if tesseract is on PATH
    path_bin = shutil.which("tesseract")
    if path_bin:
        return path_bin

    # 3. Standard Windows locations
    win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    ]
    for p in win_paths:
        if os.path.exists(p):
            return p

    return None


def is_ocr_available() -> bool:
    """Checks if Tesseract OCR is installed and runnable."""
    cmd_path = get_tesseract_command_path()
    if not cmd_path:
        return False
    try:
        pytesseract.pytesseract.tesseract_cmd = cmd_path
        pytesseract.get_tesseract_version()
        return True
    except Exception as e:
        logger.debug(f"Tesseract OCR verification check failed: {e}")
        return False


def validate_pdf(file_bytes: bytes, filename: str = "upload.pdf") -> pymupdf.Document:
    """
    Validates PDF file signature, byte limits, encryption, and document integrity.
    Returns an opened pymupdf.Document instance if valid.
    """
    settings = get_settings()
    max_bytes = settings.pdf_max_upload_size_bytes

    if not file_bytes:
        raise PDFValidationError("The uploaded file is empty (0 bytes).")

    # 1. Size check
    if len(file_bytes) > max_bytes:
        max_mb = settings.pdf_max_upload_size_mb
        actual_mb = round(len(file_bytes) / (1024 * 1024), 2)
        raise PDFValidationError(
            f"File size exceeds maximum allowed upload limit ({actual_mb}MB > {max_mb}MB)."
        )

    # 2. Header magic bytes check
    # Valid PDFs start with %PDF- (sometimes preceded by a byte-order mark or up to 1024 bytes of padding)
    header_snippet = file_bytes[:1024]
    if b"%PDF-" not in header_snippet:
        raise PDFValidationError(
            f"Invalid file format: '{filename}' does not contain a valid PDF signature."
        )

    # 3. Document structure parsing
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFValidationError(f"Unable to parse PDF document. The file may be damaged or corrupted: {e}")

    # 4. Encryption & Password check
    if getattr(doc, "is_encrypted", False) or getattr(doc, "needs_pass", False):
        doc.close()
        raise PDFValidationError("Password-protected or encrypted PDF documents are not supported. Please upload an unprotected file.")

    # 5. Page count check
    page_count = len(doc)
    if page_count == 0:
        doc.close()
        raise PDFValidationError("The uploaded PDF document contains no pages.")

    if page_count > settings.pdf_max_page_count:
        doc.close()
        raise PDFValidationError(
            f"Document exceeds maximum allowed page count ({page_count} > {settings.pdf_max_page_count} pages). Please upload a targeted job posting document."
        )

    return doc


def normalize_extracted_text(text: str) -> str:
    """
    Cleans and standardizes extracted job description text:
    - Normalizes line wrap hyphens (e.g. 'develop-\nment' -> 'development')
    - Collapses excessive empty lines while preserving paragraph boundaries
    - Strips non-printable ASCII control characters
    - Normalizes smart quotes and bullet points
    """
    if not text:
        return ""

    # Rejoin hyphenated words split across lines
    text = re.sub(r'(\b[a-zA-Z]+)-\n\s*([a-zA-Z]+\b)', r'\1\2', text)

    # Standardize bullet symbols
    text = re.sub(r'[•●■▪◆►]', '\n• ', text)

    # Remove non-printable control characters except \n, \t, \r
    text = "".join(ch for ch in text if ch in ('\n', '\t', '\r') or ch >= ' ')

    # Normalize excessive spaces per line
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]

    # Collapse more than two consecutive empty lines
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def detect_scanned_pages(doc: pymupdf.Document, min_chars: int = 80) -> Tuple[Dict[int, str], List[int]]:
    """
    Inspects each page in the document.
    Returns:
    - digital_text_map: {1_indexed_page_num: extracted_text} for pages with sufficient digital text.
    - scanned_page_nums: [1_indexed_page_num, ...] for pages with missing or insufficient text.
    """
    digital_text_map: Dict[int, str] = {}
    scanned_page_nums: List[int] = []

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]

        # Extract direct digital text
        raw_text = page.get_text("text") or ""
        clean = raw_text.strip()

        # If digital text exceeds threshold, treat as selectable digital text
        if len(clean) >= min_chars:
            digital_text_map[page_num] = clean
        else:
            # Check if there are images or very short text indicating scanned/rasterized content
            scanned_page_nums.append(page_num)

    return digital_text_map, scanned_page_nums


def run_ocr_on_page(
    page: pymupdf.Page,
    ocr_language: str = "eng",
    timeout: int = 30
) -> Tuple[str, Optional[str]]:
    """
    Renders a PyMuPDF page to a high-resolution image in memory and runs Tesseract OCR.
    Releases all temporary pixmap and image buffers immediately.
    """
    pix = None
    img = None
    warning = None

    try:
        # Render at 200 DPI (balance between sharp OCR accuracy and memory speed)
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # Convert to grayscale for OCR contrast enhancement
        if img.mode != "L":
            img = img.convert("L")

        ocr_text = pytesseract.image_to_string(
            img,
            lang=ocr_language,
            timeout=timeout
        )

        clean = ocr_text.strip()
        if len(clean) < 30:
            warning = "OCR returned minimal or low-confidence text from this page."

        return clean, warning

    except pytesseract.TesseractTimeoutError:
        logger.warning("Tesseract OCR timed out processing page.")
        return "", "OCR processing timed out on this page."
    except Exception as e:
        logger.warning(f"Error during OCR extraction: {e}")
        return "", f"OCR extraction error: {str(e)}"
    finally:
        # Free memory buffers
        if img is not None:
            try:
                img.close()
            except Exception:
                pass
        del pix


def heuristically_detect_metadata(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Scans the beginning lines of extracted text for job title and company name hints.
    """
    detected_title = None
    detected_company = None

    lines = [line.strip() for line in text.splitlines()[:25] if line.strip()]

    title_patterns = [
        re.compile(r'^(?:Job\s*Title|Position|Role|Title)\s*[:\-]\s*(.+)$', re.IGNORECASE),
        re.compile(r'^Looking\s+for\s+(?:an?|the)\s+(.+)$', re.IGNORECASE),
    ]

    company_patterns = [
        re.compile(r'^(?:Company|Organization|Employer)\s*[:\-]\s*(.+)$', re.IGNORECASE),
        re.compile(r'^(?:About|At)\s+([A-Z][A-Za-z0-9\s,\.]{2,40})(?:\s*[:\-])?$', re.IGNORECASE),
    ]

    for line in lines:
        if not detected_title:
            for pat in title_patterns:
                m = pat.match(line)
                if m:
                    cand = m.group(1).strip()
                    if 3 <= len(cand) <= 80:
                        detected_title = cand
                        break

        if not detected_company:
            for pat in company_patterns:
                m = pat.match(line)
                if m:
                    cand = m.group(1).strip()
                    if 2 <= len(cand) <= 60:
                        detected_company = cand
                        break

    return detected_title, detected_company


def extract_pdf_job_description(
    file_bytes: bytes,
    filename: str = "upload.pdf"
) -> Dict[str, Any]:
    """
    End-to-end PDF processing pipeline:
    1. Validates document size, header signature, encryption, and page bounds.
    2. Extracts digital text page-by-page.
    3. Detects scanned or image-based pages.
    4. Runs OCR only on scanned pages if Tesseract is available.
    5. Assembles complete text in exact page order.
    6. Returns extraction metadata (method: 'text' | 'ocr' | 'mixed', ocr_pages, warnings).
    """
    settings = get_settings()
    doc = validate_pdf(file_bytes, filename)
    page_count = len(doc)
    warnings: List[str] = []

    try:
        # Detect which pages have digital text and which need OCR
        digital_text_map, scanned_page_nums = detect_scanned_pages(
            doc=doc,
            min_chars=settings.pdf_min_page_text_chars
        )

        ocr_text_map: Dict[int, str] = {}
        ocr_executed_pages: List[int] = []

        if scanned_page_nums:
            # Check OCR availability
            cmd_path = get_tesseract_command_path()
            if not cmd_path or not is_ocr_available():
                # If ALL pages are scanned and OCR is unavailable, we cannot extract meaningful text
                if len(digital_text_map) == 0:
                    raise OCREngineUnavailableError(
                        f"The document '{filename}' appears to be a scanned or image-only PDF ({len(scanned_page_nums)} scanned pages), "
                        "but Tesseract OCR is not installed or configured on the server. "
                        "Please upload a PDF containing selectable digital text or install Tesseract OCR."
                    )
                else:
                    # Mixed PDF with some digital text: continue with digital pages and warn user
                    warnings.append(
                        f"Page(s) {scanned_page_nums} appear to be scanned images. Tesseract OCR is not configured, "
                        "so only selectable digital text was extracted."
                    )
            else:
                pytesseract.pytesseract.tesseract_cmd = cmd_path
                # Execute OCR on scanned pages
                for page_num in scanned_page_nums:
                    page = doc[page_num - 1]
                    page_ocr_text, page_warning = run_ocr_on_page(
                        page=page,
                        ocr_language=settings.ocr_language,
                        timeout=settings.ocr_timeout_seconds
                    )
                    ocr_text_map[page_num] = page_ocr_text
                    ocr_executed_pages.append(page_num)
                    if page_warning:
                        warnings.append(f"Page {page_num}: {page_warning}")

        # Assemble full text in correct page order
        ordered_page_texts: List[str] = []
        for p in range(1, page_count + 1):
            if p in digital_text_map:
                ordered_page_texts.append(digital_text_map[p])
            elif p in ocr_text_map and ocr_text_map[p].strip():
                ordered_page_texts.append(ocr_text_map[p])

        raw_combined = "\n\n".join(ordered_page_texts)
        clean_text = normalize_extracted_text(raw_combined)

        # Determine extraction method
        if len(ocr_executed_pages) == 0:
            extraction_method = "text"
        elif len(digital_text_map) == 0:
            extraction_method = "ocr"
        else:
            extraction_method = "mixed"

        # Check content sufficiency
        if len(clean_text) < 50:
            warnings.append(
                "The extracted text contains fewer than 50 characters. The document may be empty, blurry, or non-textual."
            )

        # Detect job title and company heuristically
        detected_title, detected_company = heuristically_detect_metadata(clean_text)

        return {
            "success": True,
            "extracted_text": clean_text,
            "page_count": page_count,
            "extraction_method": extraction_method,
            "ocr_pages": ocr_executed_pages,
            "warnings": warnings,
            "detected_job_title": detected_title,
            "detected_company_name": detected_company,
        }

    finally:
        # Guarantee document closure
        try:
            doc.close()
        except Exception:
            pass
