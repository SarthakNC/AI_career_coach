from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.job import JobAnalyzeRequest, JobResponse, JobListResponse
from services.auth_service import AuthenticatedUser, get_current_user
from services.job_analyzer import analyze_job_workflow
from services.database_service import (
    save_job_and_requirements,
    list_user_jobs,
    get_user_job_by_id,
    delete_user_job,
)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


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
