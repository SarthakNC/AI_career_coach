# CareerProof AI

> **Agentic AI platform comparing a student's verified GitHub portfolio evidence against real-world job & internship requirements.**

CareerProof AI bridges the gap between traditional resumes and actual software engineering skill evidence. Rather than relying on self-reported keywords, CareerProof AI extracts evidence-grounded skills directly from real GitHub commits and compares them to parsed job descriptions using explainable, deterministic scoring and actionable gap recommendations.

---

## Architecture & Data Flow

```
[Student / User]
       │
       ▼
[React 19 + Vite Frontend]
       │ (Bearer Token with Supabase Auth)
       ▼
[FastAPI Python Backend]
       ├── /api/v1/jobs/...               ──> [Job Retrieval & LLM Extraction]
       ├── /api/v1/github/...             ──> [GitHub REST API + Bounded Tree Ingestion]
       └── /api/v1/assessments/...        ──> [Skill Gap Assessment & Deterministic Matcher]
                                                         │
                                                         ▼
                                           [Supabase PostgreSQL (PostgREST + RLS)]
                                           ├── public.jobs & job_requirements
                                           ├── public.repositories & analysis_runs & skill_evidence
                                           └── public.assessments & assessment_requirement_results
                                               & assessment_recommendations
```

---

## Phase 7 Capabilities: AI-Powered Skill-Gap Assessment

1. **Job Requirement & Portfolio Ingestion**:
   - Integrates real job postings analyzed in Phase 5 with verified technical evidence extracted from GitHub repositories in Phase 6.
   - Evaluates requirements across single or multiple selected user repositories.

2. **Controlled Skill Normalization & Alias Mapping**:
   - Canonical normalization for technologies (e.g. `JS` &rarr; `JavaScript`, `React.js` &rarr; `React`, `Postgres` &rarr; `PostgreSQL`, `k8s` &rarr; `Kubernetes`, `Dockerfile` &rarr; `Docker`).
   - Strict false-friend protection preventing false equivalence (e.g., `Java` &ne; `JavaScript`, `C` &ne; `C++`, `Rust` &ne; `Ruby`).

3. **Evidence-Linked Requirement Matching**:
   - Categorizes every requirement as:
     - **Demonstrated** (1.0): Verified direct implementation or strong test code.
     - **Partially demonstrated** (0.5): Dependency or configuration found without full implementation depth.
     - **Not demonstrated in analyzed files** (0.0): Absence of verified evidence within analyzed repositories.
   - Attaches immutable snapshots of source file paths, line ranges, commit SHAs, and GitHub commit links.

4. **Transparent, Deterministic Scoring**:
   - Rule-based weighted average (zero LLM score fabrication):
     $$\text{Match Score} = 100 \times \frac{\sum (\text{Requirement Weight} \times \text{Status Score})}{\sum \text{Requirement Weight}}$$
   - Weights: `required` = 1.0, `preferred` = 0.5.
   - Status scores: `demonstrated` = 1.0, `partially_demonstrated` = 0.5, `not_demonstrated` = 0.0.
   - Clearly labeled as **Portfolio Evidence Match** (not a measure of innate intelligence or hiring guarantee).

5. **Prioritized Skill-Gap Analysis**:
   - Ranks deficiencies deterministically by requirement importance, status, and lack of verified code.
   - Clear explanations of why evidence is insufficient alongside existing partial evidence summaries and expected artifacts.

6. **Actionable, Grounded Portfolio Recommendations**:
   - Anti-hallucination validation ensures every recommendation references genuine requirement IDs and candidate repository IDs.
   - Distinguishes observed gaps from speculative ideas, preferring enhancements to existing repositories.

7. **Persistent Assessment History & Immutability**:
   - Persists all results to Supabase PostgreSQL under Row Level Security.
   - Reopening an assessment restores historical code snapshots and scoring parameters without silent recomputation.

---

## Phase 8 Capabilities: Automatic GitHub Change Detection & AI Career Reassessment

1. **Continuous GitHub Commit Monitoring**:
   - Background polling daemon (`workers/change_detector_worker.py`) checks monitored repositories without requiring manual "Analyze" clicks.
   - Compares latest commit SHA on the default branch with the repository's `last_analyzed_commit_sha`.
   - When the commit SHA is unchanged, expensive file ingestion and LLM calls are skipped immediately.
   - When a new commit is detected, an atomic `github_change_events` record is created using a unique idempotency key (`{repository_id}:{detected_commit_sha}`) to prevent race conditions or duplicate runs.

2. **Smart Commit Diff & Evidence Reconciliation**:
   - Queries GitHub's Compare API (`/repos/{owner}/{repo}/compare/{base}...{head}`) or Commits API to retrieve added, modified, renamed, and removed files.
   - Removed or renamed files cause immediate invalidation of obsolete skill evidence.
   - Newly added or modified code files are safely ingested within security and token bounds, updating skill evidence and storing a new `analysis_runs` record with the latest commit SHA.

3. **Automatic Assessment Recalculation & Version Lineage**:
   - Discovers any saved Phase 7 assessments referencing the updated repository.
   - Re-evaluates requirement matches and recalculates the **Portfolio Evidence Match Score** deterministically.
   - Rather than overwriting history, creates a new version (`v2`, `v3`, etc.) with `parent_assessment_id`, `trigger_event_id`, `trigger_commit_sha`, and `score_delta`.
   - Preserves complete version history so users can review earlier scores and track skill growth over time.

4. **Dedicated Repository Activity Dashboard (`/dashboard/activity`)**:
   - Displays real-time monitoring status, polling interval, and connected repositories with sync indicators.
   - One-click **"Check Changes" / Sync Now** button triggers immediate commit checks with instant feedback.
   - Detailed change event modal displays commit message, author, changed files list with patch diffs, affected skills chips, and before/after score comparisons.
   - Assessment Version Lineage modal (`v1` vs `v2`) displays score deltas and timestamped progress.

---

## Supabase Database Migrations

Run each migration script in your **Supabase Dashboard > SQL Editor**:

1. **Phase 5 Schema**: [`backend/migrations/phase5_job_analyzer.sql`](backend/migrations/phase5_job_analyzer.sql)
   - Creates `jobs` and `job_requirements` tables with RLS.
2. **Phase 6 Schema**: [`backend/migrations/phase6_github_analyzer.sql`](backend/migrations/phase6_github_analyzer.sql)
   - Creates `repositories`, `analysis_runs`, and `skill_evidence` tables with RLS and cascading deletion.
3. **Phase 7 Schema**: [`backend/migrations/phase7_skill_gap_analyzer.sql`](backend/migrations/phase7_skill_gap_analyzer.sql)
   - Creates `assessments`, `assessment_requirement_results`, and `assessment_recommendations` tables with indexes, foreign keys, and RLS policies.
4. **Phase 8 Schema**: [`backend/migrations/phase8_change_detector.sql`](backend/migrations/phase8_change_detector.sql)
   - Creates `github_change_events` table with unique idempotency key and RLS policies.
   - Alters `public.assessments` to add `version`, `parent_assessment_id`, `trigger_event_id`, `trigger_commit_sha`, and `score_delta`.
   - Alters `public.repositories` to add `monitoring_enabled`, `last_polled_at`, and `last_poll_status`.

---

## Environment Variables

### Backend Configuration (`backend/.env`):
```env
# Supabase PostgreSQL Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_publishable_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_optional

# GitHub Analysis & Phase 8 Automatic Change Detection
GITHUB_TOKEN=your_github_token_optional
GITHUB_MONITORING_ENABLED=true
GITHUB_POLL_INTERVAL_SECONDS=60
GITHUB_MAX_FILES_PER_COMMIT=50

# LLM API Configuration (Gemini or OpenAI-compatible)
LLM_API_KEY=your_gemini_or_openai_api_key
LLM_MODEL=gemini-flash-lite-latest

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend Configuration (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_anon_key
```

---

## Local Development & Worker Commands

### 1. Start the Backend API
```bash
cd backend
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

uvicorn main:app --reload --port 8000
```
API Documentation is available at: `http://localhost:8000/docs`

### 2. Start the Background Change Detector Worker
The worker can be run continuously as a daemon or on a scheduled basis:

```bash
cd backend
# Run continuously in background (daemon mode, polls every 60s):
python workers/change_detector_worker.py --daemon --interval 60

# Or run a single polling pass (useful for cron jobs or CI/CD):
python workers/change_detector_worker.py --once
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

The test suite includes **57 automated tests** covering SSRF safety, URL validation, tree filtering, secret sanitization, duplicate normalization, LLM parsing, unauthenticated access, skill normalization, deterministic scoring, gap prioritization, assessment persistence, commit diffing, idempotency keys, evidence reconciliation, and reassessment versioning:

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -v
```

---

## Judge-Ready Live Demo Checklist (Phase 8)

1. **Sign In & Setup**:
   - Log into CareerProof AI at `http://localhost:5173`.
   - Ensure you have a target job analyzed (e.g. "Full Stack Engineer") and a GitHub repository connected and analyzed.
2. **Initial Assessment (v1)**:
   - Go to **Skill Gaps** in the sidebar. Run an assessment for your job and connected repository.
   - Note the baseline **Portfolio Evidence Match Score** (e.g. 60.0%) and the requirement results.
3. **Open Repository Activity**:
   - Click **Repository Activity** in the sidebar (or navigate to `/dashboard/activity`).
   - Observe the **Monitored Repositories & Polling Status** card displaying your repository, default branch, last analyzed commit SHA, and continuous monitoring status.
4. **Push New Code to GitHub (or Trigger Sync)**:
   - Push a real commit to your repository containing added code files (e.g. adding new endpoints or tests) or click **Check Changes** to sync immediately.
   - The system detects the new commit SHA, retrieves the changed files diff, and reconciles the skill evidence pool.
5. **Review Detected Change Event**:
   - Observe the newly recorded event in the **Detected Change Events & Assessment History** list.
   - Click **View Details**:
     - Inspect the commit SHA, author, and commit message.
     - Review changed files with additions/deletions and expandable code patch diffs.
     - Review the **Reconciled Skills** chips and the updated score delta (e.g. `+15.0%`).
6. **Inspect Assessment Version Lineage (v2)**:
   - Click **View Assessment** or go to **Skill Gaps**.
   - Notice the assessment is now labeled **Version Lineage (v2)** with the updated score.
   - Click **Version Lineage**: observe the timeline modal showing `v1 (60%)` &rarr; `v2 (75%) (+15%)`, including the trigger commit SHA and timestamp.
