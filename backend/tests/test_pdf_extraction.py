import io
import uuid
from unittest.mock import patch, MagicMock

import pymupdf
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from main import app
from services.auth_service import AuthenticatedUser, get_current_user
from services.pdf_extraction_service import (
    validate_pdf,
    normalize_extracted_text,
    extract_pdf_job_description,
    PDFValidationError,
    OCREngineUnavailableError,
)
from schemas.job import LLMJobExtractionResult, LLMExtractedRequirement

client = TestClient(app)

MOCK_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
MOCK_TOKEN = "mock_pdf_test_token"


def override_current_user():
    return AuthenticatedUser(user_id=MOCK_USER_ID, token=MOCK_TOKEN, email="test_pdf@example.com")


# ─── HELPER FIXTURES: IN-MEMORY PDF GENERATORS ───

def create_digital_pdf_bytes(text: str = "Senior Full Stack Engineer\nRequirements:\n- Python and FastAPI\n- React and Tailwind CSS") -> bytes:
    """Generates an in-memory digital PDF with selectable text."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_scanned_pdf_bytes(text: str = "Scanned Position\nSkills: Docker Kubernetes PostgreSQL") -> bytes:
    """Generates an in-memory raster image and embeds it into a PDF to simulate a scanned document."""
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), text, fill=(0, 0, 0))
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")

    doc = pymupdf.open()
    page = doc.new_page(width=800, height=400)
    page.insert_image(page.rect, stream=img_buf.getvalue())
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_mixed_pdf_bytes() -> bytes:
    """Generates a 2-page PDF: Page 1 is digital text, Page 2 is a scanned image."""
    doc = pymupdf.open()
    # Page 1: Digital
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 72), "Company: Acme Corp\nJob Title: DevOps Engineer\nResponsibilities: Maintain CI/CD pipelines.", fontsize=12)

    # Page 2: Scanned image
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), "Page 2 Scanned Requirements: Terraform, AWS, Linux Administration", fill=(0, 0, 0))
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")

    p2 = doc.new_page(width=600, height=300)
    p2.insert_image(p2.rect, stream=img_buf.getvalue())

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ─── 1. CORE PDF EXTRACTION SERVICE TESTS ───

def test_extract_digital_pdf_text():
    pdf_bytes = create_digital_pdf_bytes(
        "Job Title: Senior Python Architect\n"
        "Company: Stripe\n\n"
        "Responsibilities:\n"
        "- Build scalable microservices using FastAPI and PostgreSQL.\n"
        "- Deploy containerized workloads with Docker and Kubernetes.\n"
        "- Ensure robust automated testing and high code coverage."
    )

    result = extract_pdf_job_description(pdf_bytes, "digital_jd.pdf")
    assert result["success"] is True
    assert result["page_count"] == 1
    assert result["extraction_method"] == "text"
    assert len(result["ocr_pages"]) == 0
    assert "FastAPI and PostgreSQL" in result["extracted_text"]
    assert result["detected_job_title"] == "Senior Python Architect"
    assert result["detected_company_name"] == "Stripe"


def test_extract_scanned_pdf_ocr():
    scanned_bytes = create_scanned_pdf_bytes("Job Title: Cloud Architect\nSkills Required: Docker Kubernetes Python")

    result = extract_pdf_job_description(scanned_bytes, "scanned_jd.pdf")
    assert result["success"] is True
    assert result["page_count"] == 1
    assert result["extraction_method"] == "ocr"
    assert result["ocr_pages"] == [1]
    # Check that OCR extracted the core keywords from the image
    extracted_lower = result["extracted_text"].lower()
    assert "docker" in extracted_lower or "kubernetes" in extracted_lower or "architect" in extracted_lower


def test_extract_mixed_pdf_pages():
    mixed_bytes = create_mixed_pdf_bytes()

    result = extract_pdf_job_description(mixed_bytes, "mixed_jd.pdf")
    assert result["success"] is True
    assert result["page_count"] == 2
    assert result["extraction_method"] == "mixed"
    assert 2 in result["ocr_pages"]
    assert "Acme Corp" in result["extracted_text"]


def test_extract_empty_pdf_produces_warning():
    # Create a blank PDF (valid PDF structure, but no text or images)
    doc = pymupdf.open()
    doc.new_page(width=500, height=500)
    empty_bytes = doc.tobytes()
    doc.close()

    result = extract_pdf_job_description(empty_bytes, "empty.pdf")
    assert result["success"] is True
    assert len(result["extracted_text"]) < 50
    assert any("fewer than 50 characters" in w for w in result["warnings"])


def test_text_normalization():
    raw = "We are look-\ning for a soft-\nware engineer.\n\n\n\n• Python\n● Docker"
    normalized = normalize_extracted_text(raw)
    assert "looking" in normalized
    assert "software" in normalized
    assert "\n\n\n\n" not in normalized  # Collapsed excessive newlines
    assert "• Python" in normalized


# ─── 2. SECURITY & VALIDATION TESTS ───

def test_validate_pdf_invalid_signature():
    with pytest.raises(PDFValidationError) as exc:
        validate_pdf(b"This is just a plain text file, not a real PDF.", "fake.pdf")
    assert "does not contain a valid PDF signature" in exc.value.detail


def test_validate_pdf_empty_bytes():
    with pytest.raises(PDFValidationError) as exc:
        validate_pdf(b"", "empty.pdf")
    assert "The uploaded file is empty" in exc.value.detail


def test_validate_pdf_oversized():
    # Mock settings to small size limit (e.g. 100 bytes)
    with patch("services.pdf_extraction_service.get_settings") as mock_settings:
        mock_obj = MagicMock()
        mock_obj.pdf_max_upload_size_bytes = 100
        mock_obj.pdf_max_upload_size_mb = 0.0001
        mock_settings.return_value = mock_obj

        with pytest.raises(PDFValidationError) as exc:
            validate_pdf(b"%PDF-" + b"0" * 200, "large.pdf")
        assert "exceeds maximum allowed upload limit" in exc.value.detail


def test_validate_pdf_excessive_pages():
    doc = pymupdf.open()
    for _ in range(5):
        doc.new_page()
    many_pages = doc.tobytes()
    doc.close()

    with patch("services.pdf_extraction_service.get_settings") as mock_settings:
        mock_obj = MagicMock()
        mock_obj.pdf_max_upload_size_bytes = 10 * 1024 * 1024
        mock_obj.pdf_max_page_count = 3  # Limit is 3
        mock_settings.return_value = mock_obj

        with pytest.raises(PDFValidationError) as exc:
            validate_pdf(many_pages, "many.pdf")
        assert "exceeds maximum allowed page count" in exc.value.detail


def test_validate_pdf_encrypted_fails():
    doc = pymupdf.open()
    doc.new_page()
    # Save encrypted
    perm = int(pymupdf.PDF_PERM_ACCESSIBILITY)
    encrypted_bytes = doc.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="ownerpass",
        user_pw="userpass"
    )
    doc.close()

    with pytest.raises(PDFValidationError) as exc:
        validate_pdf(encrypted_bytes, "secret.pdf")
    assert "Password-protected or encrypted" in exc.value.detail


def test_scanned_pdf_without_ocr_raises_actionable_error():
    scanned_bytes = create_scanned_pdf_bytes("Testing missing OCR")

    # Mock OCR engine unavailable
    with patch("services.pdf_extraction_service.is_ocr_available", return_value=False), \
         patch("services.pdf_extraction_service.get_tesseract_command_path", return_value=None):
        with pytest.raises(OCREngineUnavailableError) as exc:
            extract_pdf_job_description(scanned_bytes, "scanned_no_ocr.pdf")
        assert "Tesseract OCR is not installed or configured" in exc.value.detail


# ─── 3. ENDPOINT INTEGRATION TESTS ───

def test_extract_pdf_endpoint_success():
    app.dependency_overrides[get_current_user] = override_current_user
    pdf_bytes = create_digital_pdf_bytes(
        "Job Title: Senior Backend Developer\n"
        "Company: Stripe\n\n"
        "Responsibilities:\n"
        "- Design and implement distributed REST APIs using Python and FastAPI.\n"
        "- Work with relational databases like PostgreSQL."
    )

    response = client.post(
        "/api/v1/jobs/extract-pdf",
        files={"file": ("test_jd.pdf", pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["page_count"] == 1
    assert data["extraction_method"] == "text"
    assert "Python and FastAPI" in data["extracted_text"]
    app.dependency_overrides.clear()


def test_extract_pdf_endpoint_invalid_extension():
    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        "/api/v1/jobs/extract-pdf",
        files={"file": ("malicious.exe", b"fake binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Only PDF documents (.pdf) are permitted" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_extract_pdf_unauthenticated_fails():
    response = client.post(
        "/api/v1/jobs/extract-pdf",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code in (401, 422)


@patch("routes.jobs.analyze_job_workflow")
@patch("routes.jobs.save_job_and_requirements")
def test_analyze_extracted_text_endpoint(mock_save, mock_workflow):
    app.dependency_overrides[get_current_user] = override_current_user

    confirmed_text = (
        "Senior Cloud Engineer job posting.\n"
        "Must have extensive experience with AWS, Kubernetes, Terraform, and Python.\n"
        "Responsibilities include leading infrastructure automation and mentoring team members."
    )

    job_id = uuid.uuid4()
    mock_workflow.return_value = (
        confirmed_text,
        LLMJobExtractionResult(
            job_title="Senior Cloud Engineer",
            company_name="Cloud Solutions Inc",
            summary="Cloud engineering role",
            requirements=[
                LLMExtractedRequirement(skill_name="AWS", category="Deployment and DevOps", importance="required"),
                LLMExtractedRequirement(skill_name="Kubernetes", category="Deployment and DevOps", importance="required"),
                LLMExtractedRequirement(skill_name="Python", category="Programming languages", importance="required"),
            ]
        )
    )

    mock_save.return_value = {
        "id": str(job_id),
        "user_id": str(MOCK_USER_ID),
        "job_title": "Senior Cloud Engineer",
        "company_name": "Cloud Solutions Inc",
        "source_url": None,
        "description": confirmed_text,
        "summary": "Cloud engineering role",
        "created_at": "2026-10-17T07:00:00Z",
        "updated_at": "2026-10-17T07:00:00Z",
        "requirements": [
            {
                "id": str(uuid.uuid4()),
                "job_id": str(job_id),
                "skill_name": "AWS",
                "category": "Deployment and DevOps",
                "importance": "required",
                "description": None,
                "source_excerpt": None,
                "created_at": "2026-10-17T07:00:00Z",
            }
        ]
    }

    response = client.post(
        "/api/v1/jobs/analyze-extracted-text",
        json={
            "extracted_text": confirmed_text,
            "job_title": "Senior Cloud Engineer",
            "company_name": "Cloud Solutions Inc",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(job_id)
    assert data["job_title"] == "Senior Cloud Engineer"
    assert len(data["requirements"]) == 1
    app.dependency_overrides.clear()
