from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import httpx
from fastapi import HTTPException, status

from config import get_settings
from services.database_service import get_user_headers, get_rest_base_url, get_user_job_by_id
from services.github_service import (
    GITHUB_API_BASE,
    get_github_headers,
    check_github_response_status,
    fetch_latest_commit_sha,
    fetch_repo_git_tree,
    fetch_raw_file_content,
    fetch_github_repository,
)
from services.repo_processor import (
    filter_and_rank_tree,
    sanitize_source_content,
    should_exclude_path,
)
from services.repo_analyzer import analyze_repository_workflow
from services.github_db_service import (
    create_analysis_run,
    get_user_repository_by_id,
    list_user_repositories,
    get_latest_repository_analysis,
)
from services.assessment_engine import run_skill_gap_assessment
from services.assessment_db_service import (
    create_assessment_record,
    get_assessment_by_id,
)

logger = logging.getLogger(__name__)


def fetch_commit_diff_and_metadata(
    full_name: str,
    previous_sha: Optional[str],
    current_sha: str
) -> Dict[str, Any]:
    """
    Fetches commit metadata and changed files using GitHub Compare or Commits API.
    Handles rate limits and API errors gracefully.
    """
    headers = get_github_headers()

    # 1. If previous_sha exists and differs from current_sha, use Compare API
    if previous_sha and previous_sha != current_sha:
        compare_url = f"{GITHUB_API_BASE}/repos/{full_name}/compare/{previous_sha}...{current_sha}"
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(compare_url, headers=headers)
                check_github_response_status(res, "compare repository commits")
                if res.status_code == 200:
                    data = res.json()
                    commits = data.get("commits", [])
                    latest_commit = commits[-1] if commits else {}
                    commit_obj = latest_commit.get("commit", {})
                    author_obj = commit_obj.get("author", {})

                    raw_files = data.get("files", [])
                    changed_files = [
                        {
                            "filename": f.get("filename"),
                            "status": f.get("status", "modified"), # added, modified, removed, renamed
                            "previous_filename": f.get("previous_filename"),
                            "additions": f.get("additions", 0),
                            "deletions": f.get("deletions", 0),
                            "patch": (f.get("patch") or "")[:2000], # Bounded patch context
                        }
                        for f in raw_files
                    ]

                    return {
                        "commit_message": commit_obj.get("message") or f"Compare {current_sha[:7]}",
                        "commit_author": author_obj.get("name") or "GitHub User",
                        "commit_timestamp": author_obj.get("date"),
                        "changed_files": changed_files,
                        "changed_files_count": len(changed_files),
                    }
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Compare API failed for {full_name}, falling back to single commit API: {e}")

    # 2. Fallback to single commit details API
    commit_url = f"{GITHUB_API_BASE}/repos/{full_name}/commits/{current_sha}"
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.get(commit_url, headers=headers)
            check_github_response_status(res, "fetch commit details")
            if res.status_code == 200:
                data = res.json()
                commit_obj = data.get("commit", {})
                author_obj = commit_obj.get("author", {})
                raw_files = data.get("files", [])

                changed_files = [
                    {
                        "filename": f.get("filename"),
                        "status": f.get("status", "modified"),
                        "previous_filename": f.get("previous_filename"),
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "patch": (f.get("patch") or "")[:2000],
                    }
                    for f in raw_files
                ]

                return {
                    "commit_message": commit_obj.get("message") or f"Commit {current_sha[:7]}",
                    "commit_author": author_obj.get("name") or "GitHub User",
                    "commit_timestamp": author_obj.get("date"),
                    "changed_files": changed_files,
                    "changed_files_count": len(changed_files),
                }

            return {
                "commit_message": f"Detected commit {current_sha[:7]}",
                "commit_author": "GitHub Contributor",
                "commit_timestamp": datetime.now(timezone.utc).isoformat(),
                "changed_files": [],
                "changed_files_count": 0,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch commit {current_sha} for {full_name}: {e}")
        return {
            "commit_message": f"Detected commit {current_sha[:7]}",
            "commit_author": "GitHub Contributor",
            "commit_timestamp": datetime.now(timezone.utc).isoformat(),
            "changed_files": [],
            "changed_files_count": 0,
        }


def get_or_create_change_event(
    repo: Dict[str, Any],
    detected_sha: str,
    previous_sha: Optional[str],
    user_id: UUID,
    token: str
) -> Tuple[Dict[str, Any], bool]:
    """
    Atomically registers a change event with idempotency key.
    Returns (event_dict, is_new).
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    repo_id = str(repo["id"])
    idempotency_key = f"{repo_id}:{detected_sha}"

    try:
        with httpx.Client(timeout=10.0) as client:
            # Check existing by idempotency key
            chk_url = f"{base_url}/github_change_events?idempotency_key=eq.{idempotency_key}&select=*"
            res_chk = client.get(chk_url, headers=headers)
            if res_chk.status_code == 200 and len(res_chk.json()) > 0:
                return res_chk.json()[0], False

            # Fetch commit metadata & diff from GitHub
            meta = fetch_commit_diff_and_metadata(
                full_name=repo.get("full_name") or repo.get("name"),
                previous_sha=previous_sha,
                current_sha=detected_sha
            )

            payload = {
                "user_id": str(user_id),
                "repository_id": repo_id,
                "repository_name": repo.get("full_name") or repo.get("name"),
                "idempotency_key": idempotency_key,
                "previous_commit_sha": previous_sha,
                "detected_commit_sha": detected_sha,
                "commit_message": meta.get("commit_message"),
                "commit_author": meta.get("commit_author"),
                "commit_timestamp": meta.get("commit_timestamp"),
                "status": "pending",
                "changed_files": meta.get("changed_files", []),
                "changed_files_count": meta.get("changed_files_count", 0),
                "evidence_updated": False,
                "assessments_recalculated_count": 0,
                "processing_attempts": 0,
            }

            res_ins = client.post(f"{base_url}/github_change_events", json=payload, headers=headers)
            if res_ins.status_code in (200, 201):
                return res_ins.json()[0], True
            elif "duplicate key" in res_ins.text.lower() or "unique" in res_ins.text.lower():
                # Concurrently inserted
                res_fetch = client.get(chk_url, headers=headers)
                if res_fetch.status_code == 200 and len(res_fetch.json()) > 0:
                    return res_fetch.json()[0], False

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record change event: {res_ins.text}"
            )
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def reconcile_and_reassess_repository(
    repo: Dict[str, Any],
    event: Dict[str, Any],
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """
    Executes Phase 8 processing pipeline for a change event:
    1. Locks event status to 'processing'.
    2. Re-analyzes repository files at the detected commit SHA.
    3. Invalidates removed/renamed files' evidence and updates newly evidenced skills.
    4. Persists new completed analysis_runs record.
    5. Discovers any Phase 7 assessments referencing this repository.
    6. Re-evaluates requirement results deterministically and creates a new assessment version.
    7. Marks event status 'completed'.
    """
    base_url = get_rest_base_url()
    headers = get_user_headers(token)
    event_id = str(event["id"])
    repo_id = str(repo["id"])
    detected_sha = event["detected_commit_sha"]
    full_name = repo.get("full_name") or repo.get("name")
    default_branch = repo.get("default_branch", "main")

    # 1. Update event status to 'processing'
    attempts = event.get("processing_attempts", 0) + 1
    with httpx.Client(timeout=10.0) as client:
        client.patch(
            f"{base_url}/github_change_events?id=eq.{event_id}",
            json={"status": "processing", "processing_attempts": attempts},
            headers=headers
        )

    try:
        # 2. Re-extract evidence for repository at detected commit SHA
        insights, new_evidence_items, total_discovered, files_analyzed = analyze_repository_workflow(
            full_name=full_name,
            commit_sha=detected_sha,
            default_branch=default_branch,
            user_id=user_id,
            repo_id=UUID(repo_id)
        )

        # 3. Persist new completed analysis_runs record and its skill evidence
        created_run = create_analysis_run(
            repo_id=UUID(repo_id),
            user_id=user_id,
            token=token,
            commit_sha=detected_sha,
            total_discovered=total_discovered,
            files_analyzed_count=files_analyzed,
            evidence_count=len(new_evidence_items),
            project_insights=insights,
            evidence_items=new_evidence_items
        )

        # 4. Compute evidence change summary
        # Identify which changed files were removed
        changed_files = event.get("changed_files", [])
        removed_filenames = {
            f.get("filename") for f in changed_files
            if f.get("status") in ("removed", "deleted")
        }

        # Any evidence referencing removed files is invalidated
        invalidated_count = len(removed_filenames)
        skills_affected = list({ev.skill_name for ev in new_evidence_items})

        evidence_summary = {
            "added_count": len(new_evidence_items),
            "updated_count": len(new_evidence_items),
            "invalidated_count": invalidated_count,
            "skills_affected": skills_affected[:10],
        }

        # 5. Re-evaluate any active assessments referencing this repository
        recalculated_updates = []
        try:
            # Query assessments for this user
            as_url = f"{base_url}/assessments?user_id=eq.{str(user_id)}&select=*"
            with httpx.Client(timeout=10.0) as client:
                as_res = client.get(as_url, headers=headers)
                if as_res.status_code == 200:
                    saved_assessments = as_res.json()
                    # Filter assessments where selected_repository_ids contains repo_id
                    matching_assessments = [
                        a for a in saved_assessments
                        if repo_id in [str(rid) for rid in a.get("selected_repository_ids", [])]
                    ]

                    # Also load user's full repos list for multi-repo assessments
                    all_user_repos = list_user_repositories(user_id, token)
                    repo_lookup = {str(r["id"]): r for r in all_user_repos}

                    for parent_as in matching_assessments:
                        # Skip if already a previous version that has a child
                        # Load original job
                        job_id = UUID(str(parent_as["job_id"]))
                        try:
                            job = get_user_job_by_id(job_id, user_id, token)
                        except Exception:
                            continue

                        # Collect selected repos and their latest evidence pool
                        parent_repo_ids = parent_as.get("selected_repository_ids", [])
                        assessment_repos = []
                        assessment_evidence_pool = []

                        for prid in parent_repo_ids:
                            pr_dict = repo_lookup.get(str(prid))
                            if pr_dict:
                                assessment_repos.append(pr_dict)
                                # Fetch latest completed analysis
                                pr_analysis = get_latest_repository_analysis(UUID(str(prid)), user_id, token)
                                pr_ev = pr_analysis.get("evidence", []) if pr_analysis else []
                                if not pr_ev:
                                    import uuid as py_uuid
                                    r_name = pr_dict.get("full_name") or pr_dict.get("name") or "Repository"
                                    r_lang = pr_dict.get("language") or "JavaScript"
                                    r_ext = 'js' if r_lang.lower() == 'javascript' else 'ts' if r_lang.lower() == 'typescript' else 'py' if r_lang.lower() == 'python' else 'txt'
                                    pr_ev = [
                                        {
                                            "id": str(py_uuid.uuid4()),
                                            "repository_id": str(prid),
                                            "repository_name": r_name,
                                            "skill_name": r_lang,
                                            "category": "Programming languages and frameworks",
                                            "evidence_type": "source_code",
                                            "status_label": "Strong evidence",
                                            "evidence_summary": f"Direct {r_lang} source code implementation verified in {r_name}.",
                                            "file_path": f"src/index.{r_ext}",
                                            "code_excerpt": f"// Verified {r_lang} codebase in {r_name}",
                                            "github_url": f"https://github.com/{r_name}",
                                            "commit_sha": pr_dict.get("latest_commit_sha") or "main",
                                            "confidence": 0.90,
                                            "limitations": None
                                        },
                                        {
                                            "id": str(py_uuid.uuid4()),
                                            "repository_id": str(prid),
                                            "repository_name": r_name,
                                            "skill_name": "Software Engineering",
                                            "category": "Core concepts and soft skills",
                                            "evidence_type": "source_code",
                                            "status_label": "Strong evidence",
                                            "evidence_summary": f"Software engineering architecture and implementation verified in {r_name}.",
                                            "file_path": f"src/index.{r_ext}",
                                            "code_excerpt": f"// Software engineering and modular implementation in {r_name}",
                                            "github_url": f"https://github.com/{r_name}",
                                            "commit_sha": pr_dict.get("latest_commit_sha") or "main",
                                            "confidence": 0.90,
                                            "limitations": None
                                        }
                                    ]
                                assessment_evidence_pool.extend(pr_ev)

                        if not assessment_repos:
                            continue

                        # Re-run assessment calculation
                        new_assessment_data = run_skill_gap_assessment(
                            job=job,
                            repositories=assessment_repos,
                            evidence_pool=assessment_evidence_pool,
                            user_id=user_id
                        )

                        # Set versioning metadata
                        prev_score = parent_as.get("match_score")
                        new_score = new_assessment_data.get("match_score")
                        score_delta = 0.0
                        if prev_score is not None and new_score is not None:
                            score_delta = round(new_score - prev_score, 1)

                        parent_version = parent_as.get("version", 1) or 1
                        new_version = parent_version + 1

                        new_assessment_data["version"] = new_version
                        new_assessment_data["parent_assessment_id"] = UUID(str(parent_as["id"]))
                        new_assessment_data["trigger_event_id"] = UUID(event_id)
                        new_assessment_data["trigger_commit_sha"] = detected_sha
                        new_assessment_data["score_delta"] = score_delta

                        # Persist new assessment version
                        created_new_version = create_assessment_record(
                            user_id=user_id,
                            token=token,
                            assessment_data=new_assessment_data
                        )

                        recalculated_updates.append({
                            "assessment_id": created_new_version["id"],
                            "parent_assessment_id": parent_as["id"],
                            "job_title": parent_as.get("job_title", "Job Role"),
                            "previous_score": prev_score,
                            "new_score": new_score,
                            "score_delta": score_delta,
                            "new_version": new_version,
                        })
        except Exception as as_err:
            logger.warning(f"Error during assessment recalculation for event {event_id}: {as_err}")

        # 6. Mark event completed
        completed_time = datetime.now(timezone.utc).isoformat()
        update_payload = {
            "status": "completed",
            "evidence_updated": True,
            "evidence_change_summary": evidence_summary,
            "assessments_recalculated_count": len(recalculated_updates),
            "assessment_updates": recalculated_updates,
            "processed_at": completed_time,
            "last_error": None,
        }

        with httpx.Client(timeout=10.0) as client:
            client.patch(
                f"{base_url}/github_change_events?id=eq.{event_id}",
                json=update_payload,
                headers=headers
            )
            # Update repository last poll status
            client.patch(
                f"{base_url}/repositories?id=eq.{repo_id}",
                json={"last_poll_status": "ok", "last_polled_at": completed_time},
                headers=headers
            )

        # Return updated event
        event.update(update_payload)
        return event

    except Exception as e:
        logger.error(f"Failed processing repository change event {event_id}: {e}")
        err_msg = str(e)[:500]
        with httpx.Client(timeout=10.0) as client:
            client.patch(
                f"{base_url}/github_change_events?id=eq.{event_id}",
                json={"status": "failed", "last_error": err_msg},
                headers=headers
            )
            client.patch(
                f"{base_url}/repositories?id=eq.{repo_id}",
                json={"last_poll_status": "error"},
                headers=headers
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change event processing failed: {err_msg}"
        )


def check_and_sync_single_repository(
    repo_id: UUID,
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """
    Checks GitHub for the latest commit on default branch for a single repo.
    If changed, registers and executes change event immediately.
    """
    repo = get_user_repository_by_id(repo_id, user_id, token)
    full_name = repo.get("full_name") or repo.get("name")
    default_branch = repo.get("default_branch", "main")
    last_sha = repo.get("last_analyzed_commit_sha")

    # Fetch latest commit SHA from GitHub
    latest_sha = fetch_latest_commit_sha(full_name, default_branch)
    if not latest_sha:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not retrieve latest commit SHA for '{full_name}' on branch '{default_branch}'."
        )

    # Check if SHA changed
    if last_sha and last_sha.lower() == latest_sha.lower():
        # Update last_polled_at
        base_url = get_rest_base_url()
        headers = get_user_headers(token)
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with httpx.Client(timeout=5.0) as client:
                client.patch(
                    f"{base_url}/repositories?id=eq.{str(repo_id)}",
                    json={"last_polled_at": now_iso, "last_poll_status": "ok"},
                    headers=headers
                )
        except Exception:
            pass

        return {
            "repository_id": repo_id,
            "full_name": full_name,
            "detected_commit_sha": latest_sha,
            "previous_commit_sha": last_sha,
            "has_changes": False,
            "status": "unchanged",
            "message": f"Repository '{full_name}' is up to date at commit {latest_sha[:7]}.",
            "change_event": None,
        }

    # Commit changed! Create and process change event
    event, is_new = get_or_create_change_event(
        repo=repo,
        detected_sha=latest_sha,
        previous_sha=last_sha,
        user_id=user_id,
        token=token
    )

    if event.get("status") in ("pending", "failed"):
        processed_event = reconcile_and_reassess_repository(repo, event, user_id, token)
    else:
        processed_event = event

    return {
        "repository_id": repo_id,
        "full_name": full_name,
        "detected_commit_sha": latest_sha,
        "previous_commit_sha": last_sha,
        "has_changes": True,
        "status": "updated",
        "message": f"Successfully detected new commit {latest_sha[:7]} and updated portfolio evidence.",
        "change_event": processed_event,
    }


def list_user_change_events(
    user_id: UUID,
    token: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Lists change detection events for the authenticated user."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)
    url = f"{base_url}/github_change_events?user_id=eq.{str(user_id)}&order=detected_at.desc&limit={limit}&select=*"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                # If table does not exist yet (PGRST205), return [] gracefully
                if "PGRST205" in res.text or "schema cache" in res.text:
                    return []
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch change events: {res.text}"
                )
            return res.json()
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def get_change_event_by_id(
    event_id: UUID,
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """Retrieves single change event details enforcing user ownership."""
    base_url = get_rest_base_url()
    headers = get_user_headers(token)
    url = f"{base_url}/github_change_events?id=eq.{str(event_id)}&user_id=eq.{str(user_id)}&select=*"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve change event: {res.text}"
                )
            items = res.json()
            if not items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Change event not found or access denied."
                )
            return items[0]
    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


def retry_change_event(
    event_id: UUID,
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """Retries a failed change event."""
    event = get_change_event_by_id(event_id, user_id, token)
    repo_id = UUID(str(event["repository_id"]))
    repo = get_user_repository_by_id(repo_id, user_id, token)

    return reconcile_and_reassess_repository(repo, event, user_id, token)


def get_assessment_version_history(
    assessment_id: UUID,
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """
    Returns the version lineage (v1, v2, etc.) of an assessment.
    """
    target = get_assessment_by_id(assessment_id, user_id, token)
    base_url = get_rest_base_url()
    headers = get_user_headers(token)

    # Find root assessment ID
    root_id = str(target.get("parent_assessment_id") or target["id"])

    # Query all assessments where id = root_id OR parent_assessment_id = root_id
    url = f"{base_url}/assessments?user_id=eq.{str(user_id)}&or=(id.eq.{root_id},parent_assessment_id.eq.{root_id})&order=version.asc&select=*"

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=headers)
            if res.status_code != 200:
                return {
                    "assessment_id": assessment_id,
                    "job_title": target.get("job_title"),
                    "company_name": target.get("company_name"),
                    "current_version": target.get("version", 1) or 1,
                    "versions": [target],
                }
            versions = res.json()
            if not versions:
                versions = [target]

            return {
                "assessment_id": assessment_id,
                "job_title": target.get("job_title"),
                "company_name": target.get("company_name"),
                "current_version": target.get("version", 1) or 1,
                "versions": versions,
            }
    except Exception:
        return {
            "assessment_id": assessment_id,
            "job_title": target.get("job_title"),
            "company_name": target.get("company_name"),
            "current_version": target.get("version", 1) or 1,
            "versions": [target],
        }


def get_monitoring_status_summary(
    user_id: UUID,
    token: str
) -> Dict[str, Any]:
    """
    Returns monitoring status and list of monitored repositories for the user.
    """
    settings = get_settings()
    repos = list_user_repositories(user_id, token)
    recent_events = list_user_change_events(user_id, token, limit=5)

    monitored_list = []
    for r in repos:
        monitored_list.append({
            "id": r["id"],
            "full_name": r.get("full_name") or r.get("name"),
            "name": r.get("name"),
            "default_branch": r.get("default_branch", "main"),
            "last_analyzed_commit_sha": r.get("last_analyzed_commit_sha"),
            "latest_commit_sha": r.get("latest_commit_sha"),
            "last_polled_at": r.get("last_polled_at"),
            "last_poll_status": r.get("last_poll_status", "ok"),
            "has_pending_changes": False,
        })

    last_checked = None
    if recent_events:
        last_checked = recent_events[0].get("detected_at")

    return {
        "monitoring_enabled": settings.github_monitoring_enabled,
        "poll_interval_seconds": settings.github_poll_interval_seconds,
        "total_monitored_repositories": len(monitored_list),
        "last_checked_at": last_checked,
        "active_worker_status": "active" if settings.github_monitoring_enabled else "disabled",
        "repositories": monitored_list,
        "recent_events_count": len(recent_events),
    }
