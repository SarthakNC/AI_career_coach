from typing import List, Optional
from schemas.job import LLMJobExtractionResult, LLMExtractedRequirement
from services.job_fetcher import fetch_job_page
from services.job_text_extractor import extract_clean_job_text
from services.llm_service import extract_job_requirements


def normalize_requirements(requirements: List[LLMExtractedRequirement]) -> List[LLMExtractedRequirement]:
    """
    Normalizes duplicate skills while preserving meaningful distinctions.
    If the same skill name is listed multiple times under the same or different category,
    we merge them, keeping the higher importance ('required' over 'preferred')
    and the most descriptive explanation/excerpt.
    """
    seen = {}
    for req in requirements:
        # Normalize key for deduplication
        key = req.skill_name.strip().lower()
        if not key:
            continue

        if key not in seen:
            seen[key] = req
        else:
            existing = seen[key]
            # Prioritize 'required' over 'preferred'
            if req.importance == "required" and existing.importance != "required":
                existing.importance = "required"
            # Keep the longer description
            if req.description and (not existing.description or len(req.description) > len(existing.description)):
                existing.description = req.description
            # Keep the longer source excerpt
            if req.source_excerpt and (not existing.source_excerpt or len(req.source_excerpt) > len(existing.source_excerpt)):
                existing.source_excerpt = req.source_excerpt

    return list(seen.values())


def analyze_job_workflow(
    job_url: Optional[str] = None,
    pasted_description: Optional[str] = None,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None
) -> tuple[str, LLMJobExtractionResult]:
    """
    Coordinates the job analysis workflow:
    1. Determine authoritative job text:
       - If pasted_description is provided, use it (retaining job_url).
       - Else if job_url is provided, fetch it safely and extract clean text.
    2. Extract requirements with LLM.
    3. Normalize and deduplicate requirements.
    Returns (authoritative_text, validated_result).
    """
    authoritative_text = ""

    if pasted_description and len(pasted_description.strip()) >= 50:
        authoritative_text = pasted_description.strip()
    elif job_url and job_url.strip():
        html_page = fetch_job_page(job_url.strip())
        authoritative_text = extract_clean_job_text(html_page)
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a valid job posting URL or paste the job description text (minimum 50 characters)."
        )

    # Run LLM extraction
    extracted = extract_job_requirements(
        job_text=authoritative_text,
        job_title=job_title,
        company_name=company_name,
        source_url=job_url
    )

    # Deduplicate / normalize
    extracted.requirements = normalize_requirements(extracted.requirements)

    return authoritative_text, extracted
