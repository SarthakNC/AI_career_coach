from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator


# Allowed Requirement Categories
CATEGORY_LITERAL = Literal[
    "Programming languages",
    "Frameworks and libraries",
    "Backend and API development",
    "Databases and data management",
    "Testing and quality assurance",
    "Deployment and DevOps",
    "Tools and platforms",
    "Core concepts and soft skills"
]

IMPORTANCE_LITERAL = Literal["required", "preferred"]


class JobRequirementBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=150, description="Name of the skill or technology")
    category: str = Field(..., description="Organized category of the requirement")
    importance: IMPORTANCE_LITERAL = Field(default="required", description="'required' or 'preferred'")
    description: Optional[str] = Field(default=None, description="Short explanation grounded in the job source text")
    source_excerpt: Optional[str] = Field(default=None, description="Relevant excerpt from the job description")

    @field_validator("category")
    @classmethod
    def validate_or_normalize_category(cls, v: str) -> str:
        standard_categories = [
            "Programming languages",
            "Frameworks and libraries",
            "Backend and API development",
            "Databases and data management",
            "Testing and quality assurance",
            "Deployment and DevOps",
            "Tools and platforms",
            "Core concepts and soft skills"
        ]
        lower_map = {cat.lower(): cat for cat in standard_categories}
        clean_v = v.strip().lower()
        if clean_v in lower_map:
            return lower_map[clean_v]
        # Partial matches
        for cat_lower, cat_std in lower_map.items():
            if cat_lower in clean_v or clean_v in cat_lower:
                return cat_std
        return "Core concepts and soft skills"


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementResponse(JobRequirementBase):
    id: UUID
    job_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class JobAnalyzeRequest(BaseModel):
    job_url: Optional[str] = Field(default=None, description="Public job or internship posting URL")
    pasted_description: Optional[str] = Field(default=None, description="Pasted job description text")
    job_title: Optional[str] = Field(default=None, max_length=200, description="Optional job title if known")
    company_name: Optional[str] = Field(default=None, max_length=200, description="Optional company name if known")

    @field_validator("job_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class LLMExtractedRequirement(BaseModel):
    skill_name: str
    category: str
    importance: IMPORTANCE_LITERAL = "required"
    description: Optional[str] = None
    source_excerpt: Optional[str] = None


class LLMJobExtractionResult(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    summary: Optional[str] = None
    source_url: Optional[str] = None
    requirements: List[LLMExtractedRequirement] = Field(default_factory=list)


class JobResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    source_url: Optional[str] = None
    description: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requirements: List[JobRequirementResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    source_url: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    requirement_count: int = 0

    model_config = {"from_attributes": True}


class PDFExtractionResponse(BaseModel):
    success: bool = True
    extracted_text: str = Field(..., description="Full consolidated extracted text in page order")
    page_count: int = Field(..., description="Total number of pages in the PDF document")
    extraction_method: Literal["text", "ocr", "mixed"] = Field(..., description="Extraction method used ('text', 'ocr', 'mixed')")
    ocr_pages: List[int] = Field(default_factory=list, description="1-indexed page numbers that required OCR")
    warnings: List[str] = Field(default_factory=list, description="Quality or processing notices")
    detected_job_title: Optional[str] = Field(default=None, description="Optional detected job title")
    detected_company_name: Optional[str] = Field(default=None, description="Optional detected company name")


class AnalyzeExtractedTextRequest(BaseModel):
    extracted_text: str = Field(..., min_length=50, description="Confirmed extracted job description text (minimum 50 characters)")
    job_title: Optional[str] = Field(default=None, max_length=200, description="Optional job title")
    company_name: Optional[str] = Field(default=None, max_length=200, description="Optional company name")
