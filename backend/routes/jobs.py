from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from schemas.job import (
    JobAnalyzeRequest,
    JobResponse,
    JobListResponse,
    PDFExtractionResponse,
    AnalyzeExtractedTextRequest,
)
from services.auth_service import AuthenticatedUser, get_current_user
from services.job_analyzer import analyze_job_workflow
from services.pdf_extraction_service import extract_pdf_job_description
from services.database_service import (
    save_job_and_requirements,
    list_user_jobs,
    get_user_job_by_id,
    delete_user_job,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.post("/extract-pdf", response_model=PDFExtractionResponse, status_code=status.HTTP_200_OK)
async def extract_pdf(
    file: UploadFile = File(..., description="Job description PDF file (digital or scanned)"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Uploads and extracts text from a job description PDF:
    - Validates PDF signature, size limit, and page bounds.
    - Extracts selectable digital text page-by-page.
    - Automatically executes OCR on scanned/image-based pages.
    - Returns consolidated extracted text, page count, extraction method ('text' | 'ocr' | 'mixed'),
      OCR pages, and quality warnings for user preview & confirmation.
    """
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type for '{filename}'. Only PDF documents (.pdf) are permitted."
        )

    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    result = extract_pdf_job_description(file_bytes=file_bytes, filename=filename)
    return result


@router.post("/analyze-extracted-text", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def analyze_extracted_text(
    request: AnalyzeExtractedTextRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Analyzes confirmed extracted text from a PDF job description:
    1. Validates confirmed text (minimum 50 characters).
    2. Runs LLM requirement & skill extraction.
    3. Normalizes and deduplicates skills.
    4. Persists the job and extracted requirements to Supabase.
    5. Returns the structured job record ready for skill-gap assessment.
    """
    authoritative_text, extracted_result = analyze_job_workflow(
        job_url=None,
        pasted_description=request.extracted_text,
        job_title=request.job_title,
        company_name=request.company_name,
    )

    saved_record = save_job_and_requirements(
        user_id=current_user.user_id,
        token=current_user.token,
        description_text=authoritative_text,
        extracted=extracted_result,
        source_url=None
    )

    return saved_record


@router.post("/analyze", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def analyze_job(
    request: JobAnalyzeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Analyzes a job posting URL or pasted description:
    1. Verifies the user's Supabase access token.
    2. Validates and normalizes the input.
    3. Retrieves posting via SSRF-safe fetcher if URL provided.
    4. Extracts requirements using LLM.
    5. Normalizes and validates the structured response.
    6. Saves the job and requirements to Supabase with user identity.
    7. Returns the saved job analysis.
    """
    authoritative_text, extracted_result = analyze_job_workflow(
        job_url=request.job_url,
        pasted_description=request.pasted_description,
        job_title=request.job_title,
        company_name=request.company_name,
    )

    saved_record = save_job_and_requirements(
        user_id=current_user.user_id,
        token=current_user.token,
        description_text=authoritative_text,
        extracted=extracted_result,
        source_url=request.job_url
    )

    return saved_record


@router.get("", response_model=List[JobListResponse], status_code=status.HTTP_200_OK)
def get_jobs(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns the authenticated user's saved job analyses, newest first.
    Enforces user isolation via user_id and RLS.
    """
    return list_user_jobs(user_id=current_user.user_id, token=current_user.token)


@router.get("/{job_id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
def get_job(
    job_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns a single job analysis with full requirements list belonging to the authenticated user.
    """
    return get_user_job_by_id(job_id=job_id, user_id=current_user.user_id, token=current_user.token)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Deletes an analysis belonging to the authenticated user with cascading deletion.
    """
    delete_user_job(job_id=job_id, user_id=current_user.user_id, token=current_user.token)
    return None
