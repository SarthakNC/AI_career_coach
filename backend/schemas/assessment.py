from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


ASSESSMENT_STATUS_LITERAL = Literal["demonstrated", "partially_demonstrated", "not_demonstrated"]
RECOMMENDATION_PRIORITY_LITERAL = Literal["high", "medium", "low"]


# Request to generate an assessment
class AssessmentCreateRequest(BaseModel):
    job_id: UUID = Field(..., description="ID of the previously analyzed job")
    repository_ids: List[UUID] = Field(..., min_length=1, description="List of successfully analyzed repository IDs")


# Assessment Options: Available Jobs and Analyzed Repositories
class AssessmentOptionJob(BaseModel):
    id: UUID
    job_title: Optional[str] = "Untitled Role"
    company_name: Optional[str] = "Unknown Company"
    source_url: Optional[str] = None
    requirement_count: int = 0
    created_at: datetime


class AssessmentOptionRepo(BaseModel):
    id: UUID
    full_name: str
    name: str
    language: Optional[str] = None
    latest_analysis_id: Optional[UUID] = None
    last_analyzed_commit_sha: Optional[str] = None
    evidence_count: int = 0
    analyzed_at: Optional[str] = None


class AssessmentOptionsResponse(BaseModel):
    jobs: List[AssessmentOptionJob] = Field(default_factory=list)
    repositories: List[AssessmentOptionRepo] = Field(default_factory=list)


# Requirement Assessment Result
class RequirementResultItem(BaseModel):
    id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
    skill_name: str
    normalized_skill_name: str
    category: str
    importance: str = "required"
    requirement_weight: float = 1.0
    status: ASSESSMENT_STATUS_LITERAL
    status_score: float = 0.0
    score_contribution: float = 0.0
    explanation: str
    supporting_evidence_ids: List[UUID] = Field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: Optional[str] = None
    suggested_next_step: Optional[str] = None

    model_config = {"from_attributes": True}


# Prioritized Gap
class PrioritizedGapItem(BaseModel):
    requirement_id: Optional[UUID] = None
    skill_name: str
    category: str
    importance: str
    status: ASSESSMENT_STATUS_LITERAL
    status_score: float
    gap_reason: str
    existing_evidence_summary: Optional[str] = None
    suggested_action: str
    expected_artifact: str


# Portfolio Recommendation
class AssessmentRecommendationItem(BaseModel):
    id: Optional[UUID] = None
    title: str
    related_requirement_ids: List[UUID] = Field(default_factory=list)
    related_skills: List[str] = Field(default_factory=list)
    priority: RECOMMENDATION_PRIORITY_LITERAL = "medium"
    reason: str
    suggested_task: str
    expected_artifact: str
    evidence_to_produce: str
    related_repository_id: Optional[UUID] = None
    related_repository_name: Optional[str] = None
    estimated_effort: Optional[str] = None
    limitations: Optional[str] = None

    model_config = {"from_attributes": True}


# Score Breakdown and Explanation
class ScoreExplanation(BaseModel):
    method: str = "weighted_average_v1"
    match_score: Optional[float] = None
    total_requirements: int = 0
    demonstrated_count: int = 0
    partially_demonstrated_count: int = 0
    not_demonstrated_count: int = 0
    required_count: int = 0
    preferred_count: int = 0
    required_demonstrated_ratio: Optional[float] = None
    weight_formula: str = "Match Score = 100 * sum(weight * status_score) / sum(weight)"
    status_weights: Dict[str, float] = {
        "demonstrated": 1.0,
        "partially_demonstrated": 0.5,
        "not_demonstrated": 0.0
    }
    importance_weights: Dict[str, float] = {
        "required": 1.0,
        "preferred": 0.5
    }
    methodology_note: str = (
        "Deterministic portfolio evidence match score reflecting directly verifiable "
        "evidence found in analyzed repository files. It does not measure personal ability or guarantee employment."
    )


# Complete Assessment Detail Response
class AssessmentDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    selected_repository_ids: List[UUID] = Field(default_factory=list)
    repositories_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "completed"
    match_score: Optional[float] = None
    scoring_method: str = "weighted_average_v1"
    total_requirements: int = 0
    demonstrated_count: int = 0
    partially_demonstrated_count: int = 0
    not_demonstrated_count: int = 0
    score_explanation: ScoreExplanation
    assessment_limitations: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    requirement_results: List[RequirementResultItem] = Field(default_factory=list)
    prioritized_gaps: List[PrioritizedGapItem] = Field(default_factory=list)
    recommendations: List[AssessmentRecommendationItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# Assessment Summary for History List
class AssessmentSummaryResponse(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    selected_repository_ids: List[UUID] = Field(default_factory=list)
    status: str = "completed"
    match_score: Optional[float] = None
    total_requirements: int = 0
    demonstrated_count: int = 0
    partially_demonstrated_count: int = 0
    not_demonstrated_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
