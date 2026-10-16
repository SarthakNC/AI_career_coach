from typing import Any, Dict, List, Optional
from uuid import UUID
import httpx
from fastapi import HTTPException, status
from config import get_settings
from schemas.job import JobResponse, JobListResponse, LLMJobExtractionResult


def get_user_headers(token: str) -> Dict[str, str]:
    """Builds headers for Supabase PostgREST scoped to authenticated user token."""
    settings = get_settings()
    # In PostgREST, 'apikey' can be the anon key, but 'Authorization' must carry user's Bearer token.
    # If service_role_key is configured, it can be used for server operations, but with user token, RLS applies natively.
    apikey = settings.supabase_key or ""
    return {
        "apikey": apikey,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_rest_base_url() -> str:
    settings = get_settings()
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is not configured (SUPABASE_URL is missing)."
        )
    return settings.supabase_url.rstrip("/") + "/rest/v1"


def save_job_and_requirements(
    user_id: UUID,
    token: str,
    description_text: str,
    extracted: LLMJobExtractionResult,
    source_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Persists job analysis and its extracted requirements into Supabase.
    Enforces that user_id is the verified identity from the token.
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    job_payload = {
        "user_id": str(user_id),
        "job_title": extracted.job_title,
        "company_name": extracted.company_name,
        "source_url": source_url or extracted.source_url,
        "description": description_text,
        "summary": extracted.summary,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            # 1. Insert job
            res = client.post(f"{base_url}/jobs", json=job_payload, headers=headers)
            if res.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save job record to database: {res.text}"
                )
            created_job_list = res.json()
            if not created_job_list or not isinstance(created_job_list, list):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database returned invalid response when creating job."
                )
            created_job = created_job_list[0]
            job_id = created_job["id"]

            # 2. Insert requirements in bulk
            req_payloads = [
                {
                    "job_id": job_id,
                    "skill_name": req.skill_name,
                    "category": req.category,
                    "importance": req.importance,
                    "description": req.description,
                    "source_excerpt": req.source_excerpt,
                }
                for req in extracted.requirements
            ]

            saved_requirements = []
            if req_payloads:
                req_res = client.post(f"{base_url}/job_requirements", json=req_payloads, headers=headers)
                if req_res.status_code not in (200, 201):
                    # Clean up orphaned job if requirements insert fails
                    client.delete(f"{base_url}/jobs?id=eq.{job_id}", headers=headers)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to save job requirements: {req_res.text}"
                    )
                saved_requirements = req_res.json()

            created_job["requirements"] = saved_requirements
            return created_job

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def list_user_jobs(user_id: UUID, token: str) -> List[Dict[str, Any]]:
    """Fetches user's saved jobs, newest first."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    # Query jobs ordered by created_at desc with requirements count
    url = f"{base_url}/jobs?select=*,job_requirements(id)&order=created_at.desc"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch jobs: {res.text}"
                )
            jobs_data = res.json()
            results = []
            for item in jobs_data:
                reqs = item.pop("job_requirements", [])
                item["requirement_count"] = len(reqs) if isinstance(reqs, list) else 0
                results.append(item)
            return results
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_user_job_by_id(job_id: UUID, user_id: UUID, token: str) -> Dict[str, Any]:
    """Fetches single job with nested job_requirements, verifying ownership."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/jobs?id=eq.{str(job_id)}&select=*,job_requirements(*)"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch job details: {res.text}"
                )
            jobs = res.json()
            if not jobs or len(jobs) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job analysis not found or you do not have permission to access it."
                )
            job = jobs[0]
            # Verify user_id match
            if str(job.get("user_id")) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this job analysis."
                )
            job["requirements"] = job.pop("job_requirements", [])
            return job
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def delete_user_job(job_id: UUID, user_id: UUID, token: str) -> None:
    """Deletes a job belonging to the authenticated user. Cascades to requirements."""
    # First verify job exists and belongs to user
    get_user_job_by_id(job_id, user_id, token)

    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    url = f"{base_url}/jobs?id=eq.{str(job_id)}&user_id=eq.{str(user_id)}"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.delete(url, headers=headers)
            if res.status_code not in (200, 204):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete job: {res.text}"
                )
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )
