from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.auth_service import AuthenticatedUser, get_current_user
from schemas.change_detection import (
    ChangeEventResponse,
    ChangeEventListResponse,
    MonitoringStatusResponse,
    SyncRepositoryResponse,
    AssessmentVersionHistoryResponse,
)
from services.change_detector_service import (
    get_monitoring_status_summary,
    check_and_sync_single_repository,
    list_user_change_events,
    get_change_event_by_id,
    retry_change_event,
    get_assessment_version_history,
)

router = APIRouter(prefix="/api/v1/github", tags=["GitHub Change Detection & Monitoring"])


@router.get("/monitoring/status", response_model=MonitoringStatusResponse, status_code=status.HTTP_200_OK)
def get_monitoring_status(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Returns monitoring status, polling interval, and repository synchronization
    information for all connected repositories belonging to the authenticated user.
    """
    return get_monitoring_status_summary(
        user_id=current_user.user_id,
        token=current_user.token
    )


@router.post("/repositories/{repository_id}/sync", response_model=SyncRepositoryResponse, status_code=status.HTTP_200_OK)
def sync_repository(
    repository_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Triggers an immediate synchronization check for a connected repository.
    Fetches the latest commit SHA from GitHub. If changed, ingests the commit diff,
    reconciles skill evidence, and automatically triggers skill-gap reassessments.
    """
    return check_and_sync_single_repository(
        repo_id=repository_id,
        user_id=current_user.user_id,
        token=current_user.token
    )


@router.get("/changes", response_model=ChangeEventListResponse, status_code=status.HTTP_200_OK)
def list_change_events(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Lists persisted repository change events for the authenticated user,
    ordered by detection time descending.
    """
    events = list_user_change_events(
        user_id=current_user.user_id,
        token=current_user.token,
        limit=limit
    )
    return ChangeEventListResponse(
        events=events,
        total=len(events)
    )


@router.get("/changes/{change_id}", response_model=ChangeEventResponse, status_code=status.HTTP_200_OK)
def get_change_event(
    change_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retrieves full details of a change event, including commit diff,
    changed files, processing status, evidence summary, and assessment score updates.
    """
    return get_change_event_by_id(
        event_id=change_id,
        user_id=current_user.user_id,
        token=current_user.token
    )


@router.post("/changes/{change_id}/retry", response_model=ChangeEventResponse, status_code=status.HTTP_200_OK)
def retry_failed_change_event(
    change_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Retries processing a failed change event safely with ownership verification.
    """
    return retry_change_event(
        event_id=change_id,
        user_id=current_user.user_id,
        token=current_user.token
    )
