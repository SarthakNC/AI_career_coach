from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

CHANGE_EVENT_STATUS_LITERAL = Literal["pending", "processing", "completed", "failed", "skipped"]


class ChangedFileItem(BaseModel):
    filename: str
    status: Literal["added", "modified", "removed", "renamed"]
    previous_filename: Optional[str] = None
    additions: Optional[int] = 0
    deletions: Optional[int] = 0
    patch: Optional[str] = None


class EvidenceChangeSummary(BaseModel):
    added_count: int = 0
    updated_count: int = 0
    invalidated_count: int = 0
    skills_affected: List[str] = Field(default_factory=list)


class AssessmentUpdateSummary(BaseModel):
    assessment_id: UUID
    job_title: Optional[str] = "Job Role"
    previous_score: Optional[float] = None
    new_score: Optional[float] = None
    score_delta: float = 0.0
    new_version: int = 2


class ChangeEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    repository_id: UUID
    repository_name: str
    idempotency_key: str
    previous_commit_sha: Optional[str] = None
    detected_commit_sha: str
    commit_message: Optional[str] = None
    commit_author: Optional[str] = None
    commit_timestamp: Optional[datetime] = None
    status: CHANGE_EVENT_STATUS_LITERAL
    changed_files: List[ChangedFileItem] = Field(default_factory=list)
    changed_files_count: int = 0
    evidence_updated: bool = False
    evidence_change_summary: Optional[EvidenceChangeSummary] = None
    assessments_recalculated_count: int = 0
    assessment_updates: List[AssessmentUpdateSummary] = Field(default_factory=list)
    processing_attempts: int = 0
    last_error: Optional[str] = None
    detected_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeEventListResponse(BaseModel):
    events: List[ChangeEventResponse] = Field(default_factory=list)
    total: int = 0


class MonitoredRepositorySummary(BaseModel):
    id: UUID
    full_name: str
    name: str
    default_branch: str
    last_analyzed_commit_sha: Optional[str] = None
    latest_commit_sha: Optional[str] = None
    last_polled_at: Optional[datetime] = None
    last_poll_status: str = "ok"
    has_pending_changes: bool = False


class MonitoringStatusResponse(BaseModel):
    monitoring_enabled: bool = True
    poll_interval_seconds: int = 60
    total_monitored_repositories: int = 0
    last_checked_at: Optional[datetime] = None
    active_worker_status: str = "idle"
    repositories: List[MonitoredRepositorySummary] = Field(default_factory=list)
    recent_events_count: int = 0


class SyncRepositoryResponse(BaseModel):
    repository_id: UUID
    full_name: str
    detected_commit_sha: str
    previous_commit_sha: Optional[str] = None
    has_changes: bool
    status: str
    message: str
    change_event: Optional[ChangeEventResponse] = None


class AssessmentVersionHistoryItem(BaseModel):
    id: UUID
    version: int
    parent_assessment_id: Optional[UUID] = None
    trigger_event_id: Optional[UUID] = None
    trigger_commit_sha: Optional[str] = None
    match_score: Optional[float] = None
    score_delta: float = 0.0
    total_requirements: int = 0
    demonstrated_count: int = 0
    partially_demonstrated_count: int = 0
    not_demonstrated_count: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None


class AssessmentVersionHistoryResponse(BaseModel):
    assessment_id: UUID
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    current_version: int = 1
    versions: List[AssessmentVersionHistoryItem] = Field(default_factory=list)
