"""
Parivartan AI — Phase 8: Automatic GitHub Change Detection & AI Career Reassessment
Background Worker Daemon & Scheduled Poller

Usage:
    # Run once (single pass over all monitored repositories, then exit):
    python workers/change_detector_worker.py --once

    # Run continuously as a background daemon (polls every N seconds):
    python workers/change_detector_worker.py --daemon --interval 60

Environment variables:
    GITHUB_MONITORING_ENABLED (default: true)
    GITHUB_POLL_INTERVAL_SECONDS (default: 60)
    GITHUB_TOKEN (GitHub personal access token for higher rate limits)
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY
"""

import argparse
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import get_settings
from services.github_service import fetch_latest_commit_sha
from services.change_detector_service import (
    get_or_create_change_event,
    reconcile_and_reassess_repository,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("change_detector_worker")

# Global flag for graceful shutdown
_running = True


def signal_handler(signum, frame):
    global _running
    logger.info("Received termination signal (%s). Shutting down worker gracefully...", signum)
    _running = False


def get_worker_db_headers() -> Dict[str, str]:
    """
    Returns authorization headers for the worker.
    Uses SUPABASE_SERVICE_ROLE_KEY if provided, falling back to SUPABASE_KEY.
    """
    settings = get_settings()
    key = settings.supabase_service_role_key or settings.supabase_key or ""
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def get_worker_rest_url() -> str:
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured.")
    return settings.supabase_url.rstrip("/") + "/rest/v1"


def fetch_all_monitored_repositories() -> List[Dict[str, Any]]:
    """
    Queries Supabase for all repositories eligible for monitoring.
    Falls back gracefully if monitoring_enabled column is not yet migrated.
    """
    base_url = get_worker_rest_url()
    headers = get_worker_db_headers()

    try:
        with httpx.Client(timeout=10.0) as client:
            # First try with monitoring_enabled filter
            url = f"{base_url}/repositories?select=*"
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                repos = res.json()
                # Filter in Python to tolerate environments with or without the column
                return [r for r in repos if r.get("monitoring_enabled", True) is not False]
            elif "PGRST205" in res.text or "schema cache" in res.text:
                logger.warning("repositories table not found in Supabase schema cache.")
                return []
            else:
                logger.error("Failed to query repositories: HTTP %s - %s", res.status_code, res.text)
                return []
    except Exception as e:
        logger.error("Exception fetching monitored repositories: %s", e)
        return []


def update_repository_poll_status(repo_id: str, status_val: str, sha: Optional[str] = None):
    """Updates repository last_polled_at, last_poll_status, and latest_commit_sha."""
    base_url = get_worker_rest_url()
    headers = get_worker_db_headers()
    now_iso = datetime.now(timezone.utc).isoformat()

    payload: Dict[str, Any] = {
        "last_polled_at": now_iso,
        "last_poll_status": status_val,
    }
    if sha:
        payload["latest_commit_sha"] = sha

    try:
        with httpx.Client(timeout=5.0) as client:
            client.patch(f"{base_url}/repositories?id=eq.{repo_id}", json=payload, headers=headers)
    except Exception as e:
        logger.debug("Could not update repository poll status: %s", e)


def process_single_repository(repo: Dict[str, Any]) -> bool:
    """
    Polls a single repository for new commits:
    - If unchanged, skips.
    - If changed, creates change event and executes reconciliation pipeline.
    Returns True if a new commit was detected and processed.
    """
    repo_id = str(repo.get("id"))
    full_name = repo.get("full_name") or repo.get("name")
    default_branch = repo.get("default_branch", "main")
    user_id_str = str(repo.get("user_id"))
    last_sha = repo.get("last_analyzed_commit_sha")

    if not full_name or not user_id_str:
        return False

    user_id = UUID(user_id_str)
    settings = get_settings()
    auth_token = settings.supabase_service_role_key or settings.supabase_key or ""

    # 1. Fetch latest commit SHA from GitHub
    try:
        latest_sha = fetch_latest_commit_sha(full_name, default_branch)
    except Exception as gh_err:
        logger.warning("[%s] GitHub check failed: %s", full_name, gh_err)
        update_repository_poll_status(repo_id, "error")
        return False

    if not latest_sha:
        update_repository_poll_status(repo_id, "not_found")
        return False

    # 2. Check if commit SHA is unchanged
    if last_sha and last_sha.lower() == latest_sha.lower():
        update_repository_poll_status(repo_id, "ok", latest_sha)
        logger.debug("[%s] Up to date (SHA: %s)", full_name, latest_sha[:7])
        return False

    # 3. New commit detected!
    logger.info(
        "[%s] New commit detected! Previous: %s -> New: %s",
        full_name,
        (last_sha[:7] if last_sha else "none"),
        latest_sha[:7],
    )

    try:
        # Atomic change event registration with idempotency
        event, is_new = get_or_create_change_event(
            repo=repo,
            detected_sha=latest_sha,
            previous_sha=last_sha,
            user_id=user_id,
            token=auth_token,
        )

        if not is_new and event.get("status") in ("completed", "processing"):
            logger.info("[%s] Change event for SHA %s already in state '%s'.", full_name, latest_sha[:7], event.get("status"))
            return False

        # Execute reconciliation & automatic reassessments
        processed = reconcile_and_reassess_repository(
            repo=repo,
            event=event,
            user_id=user_id,
            token=auth_token,
        )

        as_count = processed.get("assessments_recalculated_count", 0)
        logger.info(
            "[%s] Successfully reconciled commit %s. Assessments updated: %d",
            full_name,
            latest_sha[:7],
            as_count,
        )
        update_repository_poll_status(repo_id, "ok", latest_sha)
        return True

    except Exception as proc_err:
        logger.error("[%s] Error processing change event: %s", full_name, proc_err)
        update_repository_poll_status(repo_id, "error", latest_sha)
        return False


def run_monitoring_cycle() -> int:
    """
    Executes a complete scan across all monitored repositories.
    Returns the count of repositories with new commits processed.
    """
    settings = get_settings()
    if not settings.github_monitoring_enabled:
        logger.info("GitHub monitoring is disabled in configuration (GITHUB_MONITORING_ENABLED=False).")
        return 0

    repos = fetch_all_monitored_repositories()
    if not repos:
        logger.debug("No monitored repositories found.")
        return 0

    logger.info("Starting monitoring cycle for %d repository/repositories...", len(repos))
    updated_count = 0

    for repo in repos:
        if not _running:
            break
        try:
            if process_single_repository(repo):
                updated_count += 1
        except Exception as e:
            logger.error("Unhandled error polling %s: %s", repo.get("full_name"), e)

    logger.info("Monitoring cycle completed. %d repository/repositories updated.", updated_count)
    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Parivartan AI — Automatic GitHub Change Detector Worker")
    parser.add_argument("--once", action="store_true", help="Run a single polling cycle and exit.")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in a loop.")
    parser.add_argument("--interval", type=int, default=None, help="Polling interval in seconds (default from config or 60).")

    args = parser.parse_args()

    # Register OS signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    settings = get_settings()
    interval = args.interval or settings.github_poll_interval_seconds or 60

    logger.info(
        "Parivartan AI Change Detector Worker started (Interval: %ds, Monitoring: %s)",
        interval,
        settings.github_monitoring_enabled,
    )

    if args.once:
        run_monitoring_cycle()
        logger.info("Single pass completed. Exiting worker.")
        sys.exit(0)

    # Daemon mode (default if not --once)
    while _running:
        start_time = time.time()
        try:
            run_monitoring_cycle()
        except Exception as cycle_err:
            logger.error("Error during monitoring cycle: %s", cycle_err)

        # Sleep for remainder of interval, checking _running periodically
        elapsed = time.time() - start_time
        sleep_needed = max(1.0, interval - elapsed)

        sleep_chunks = int(sleep_needed)
        for _ in range(sleep_chunks):
            if not _running:
                break
            time.sleep(1.0)
        if _running:
            fraction = sleep_needed - sleep_chunks
            if fraction > 0:
                time.sleep(fraction)

    logger.info("Change detector worker has cleanly terminated.")


if __name__ == "__main__":
    main()
