from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Resolve / Search input
class GitHubResolveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="GitHub username or repository URL / full_name")

    @field_validator("query")
    @classmethod
    def clean_query(cls, v: str) -> str:
        return v.strip()


class GitHubResolvedItem(BaseModel):
    type: Literal["user", "repository"]
    username: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    repositories: Optional[List[Dict[str, Any]]] = None


class RepositoryAddRequest(BaseModel):
    full_name: str = Field(..., description="e.g. 'octocat/Hello-World'")
    github_id: Optional[int] = None
    name: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    html_url: Optional[str] = None
    default_branch: Optional[str] = "main"
    language: Optional[str] = None
    stargazers_count: Optional[int] = 0
    forks_count: Optional[int] = 0
    open_issues_count: Optional[int] = 0
    is_fork: Optional[bool] = False
    is_private: Optional[bool] = False
    latest_commit_sha: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    github_id: Optional[int] = None
    full_name: str
    name: str
    owner: str
    description: Optional[str] = None
    html_url: str
    default_branch: str
    language: Optional[str] = None
    languages_breakdown: Optional[Dict[str, int]] = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    is_fork: bool = False
    is_private: bool = False
    latest_commit_sha: Optional[str] = None
    last_analyzed_commit_sha: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_analysis: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class SkillEvidenceItem(BaseModel):
    id: Optional[UUID] = None
    analysis_run_id: Optional[UUID] = None
    repository_id: Optional[UUID] = None
    skill_name: str
    category: str
    evidence_type: Literal["source_code", "test", "configuration", "dependency", "documentation"]
    status_label: Literal["Strong evidence", "Some evidence", "Mentioned only", "Not demonstrated in analyzed files"] = "Strong evidence"
    evidence_summary: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_excerpt: Optional[str] = None
    github_url: Optional[str] = None
    commit_sha: str
    confidence: float = 0.85
    limitations: Optional[str] = None

    model_config = {"from_attributes": True}


# Project Quality & Architecture schemas
class TechStackItem(BaseModel):
    name: str
    category: str
    evidence_type: str
    detection_source: str
    is_direct_implementation: bool = True


class ArchitectureInsight(BaseModel):
    summary: str
    components: List[Dict[str, str]] = Field(default_factory=list)
    diagram_mermaid: Optional[str] = None
    basis_explanation: Optional[str] = None


class EngineeringPractice(BaseModel):
    practice: str
    status: Literal["present", "incomplete", "unverified"]
    evidence: str
    recommendation: Optional[str] = None


class ProjectStrength(BaseModel):
    title: str
    explanation: str
    evidence_source: str
    why_useful: str


class ImprovementOpportunity(BaseModel):
    title: str
    priority: Literal["high", "medium", "low"]
    issue_explanation: str
    evidence_source: Optional[str] = None
    suggested_improvement: str
    is_directly_observed: bool = True
    confidence: Optional[str] = "medium"


class AnalysisCoverage(BaseModel):
    total_files_discovered: int
    files_analyzed_count: int
    files_skipped_count: int
    skipped_reasons: List[str] = Field(default_factory=list)
    commit_sha: str
    analysis_timestamp: str
    is_static_analysis: bool = True
    limitations: str


class ProjectInsights(BaseModel):
    tech_stack: List[TechStackItem] = Field(default_factory=list)
    architecture: ArchitectureInsight
    engineering_practices: List[EngineeringPractice] = Field(default_factory=list)
    strengths: List[ProjectStrength] = Field(default_factory=list)
    improvements: List[ImprovementOpportunity] = Field(default_factory=list)
    coverage: Optional[AnalysisCoverage] = None


class AnalysisRunResponse(BaseModel):
    id: UUID
    repository_id: UUID
    user_id: UUID
    commit_sha: str
    status: Literal["pending", "running", "completed", "failed"]
    total_files_discovered: int
    files_analyzed_count: int
    evidence_count: int
    project_insights: Optional[Dict[str, Any]] = None
    error_summary: Optional[str] = None
    analysis_limitations: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    evidence: List[SkillEvidenceItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PortfolioSummaryResponse(BaseModel):
    total_repositories: int
    analyzed_repositories: int
    total_skills_detected: int
    latest_analyzed_at: Optional[str] = None
