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

## PDF Job Description Extraction & OCR Architecture

CareerProof AI supports direct PDF job description ingestion for both digital vector PDFs and scanned/rasterized documents.

```
[Uploaded PDF]
      │
      ▼
[validate_pdf] ──> Check Magic Bytes (%PDF-), File Size (<= 10MB), Page Bounds (<= 30), Encryption
      │
      ▼
[detect_scanned_pages]
      ├── Page has >= 80 chars digital text ──> [Direct PyMuPDF Text Extraction]
      │                                                                  │
      └── Page has < 80 chars (Scanned)     ──> [200 DPI Grayscale Render]
                                                                         │
                                                                         ▼
                                                       [Tesseract OCR Engine]
                                                                         │
                                                                         ▼
[normalize_extracted_text] ──> De-hyphenate, bullet points, clean whitespace, page ordering
      │
      ▼
[Editable Frontend Preview] ──> User inspects, edits & confirms extracted job text
      │
      ▼
[POST /api/v1/jobs/analyze-extracted-text] ──> LLM Skill Extraction ──> ChromaDB RAG Assessment
```

### Key Technical Highlights

1. **Selective Hybrid Processing**:
   - Only pages lacking selectable text undergo rasterization and OCR. Digital pages extract instantly with zero OCR overhead.
   - Preserves reading flow across multi-page and mixed documents.
2. **Pure Python/C Rendering**:
   - Uses PyMuPDF's built-in `page.get_pixmap(dpi=200)` to render scanned pages to memory buffers, eliminating external Poppler/PDF2Image dependencies.
3. **Editable Human-in-the-Loop Preview**:
   - The user reviews, formats, and approves the extracted text before any LLM token usage or database persistence.
4. **Resilient Error Handling**:
   - Rejects encrypted/password-protected PDFs, oversized files (> 10MB), and files exceeding page limits (> 30 pages) with actionable HTTP 400 messages.
   - If a scanned document requires OCR but Tesseract is not installed, the API returns HTTP 422 with clear installation instructions rather than failing silently.

---

## Installation & OCR Setup

### 1. Python Dependencies
In `backend/`:
```bash
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```
Key packages: `pymupdf>=1.24.0`, `pytesseract>=0.3.10`, `pillow>=10.0.0`, `python-multipart>=0.0.12`.

### 2. Tesseract OCR Engine Installation

#### Windows Setup:
1. Download the official Windows installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to the default directory: `C:\Program Files\Tesseract-OCR`
3. The backend automatically detects Tesseract at this path or on your system `PATH`.
4. (Optional) Explicitly configure the path in `backend/.env`:
   ```env
   OCR_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

#### Linux / Ubuntu / Debian Setup:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
```

#### macOS Setup:
```bash
brew install tesseract
```

---

## Environment Configuration

Configure the following variables in `backend/.env`:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PDF_MAX_UPLOAD_SIZE_MB` | `10` | Maximum allowed upload size in megabytes |
| `PDF_MAX_PAGE_COUNT` | `30` | Maximum pages allowed per PDF document |
| `OCR_LANGUAGE` | `eng` | Tesseract language model (e.g. `eng`) |
| `OCR_TESSERACT_CMD` | `None` | Custom path to `tesseract` binary if not in PATH |
| `OCR_TIMEOUT_SECONDS` | `30` | Timeout in seconds per page OCR execution |
| `PDF_MIN_PAGE_TEXT_CHARS` | `80` | Min character threshold before triggering OCR |

---

## PDF Extraction API Endpoints

### 1. Extract Text from PDF
**`POST /api/v1/jobs/extract-pdf`** (Multipart Form Data)
- **Headers**: `Authorization: Bearer <supabase_token>`
- **Body**: `file: <binary_pdf>`

**Example Response**:
```json
{
  "success": true,
  "extracted_text": "Senior Backend Engineer\nResponsibilities:\n- Design scalable APIs with FastAPI\n- PostgreSQL and Redis caching",
  "page_count": 2,
  "extraction_method": "mixed",
  "ocr_pages": [2],
  "warnings": [],
  "detected_job_title": "Senior Backend Engineer",
  "detected_company_name": null
}
```

### 2. Analyze Confirmed Extracted Text
**`POST /api/v1/jobs/analyze-extracted-text`** (JSON)
- **Headers**: `Authorization: Bearer <supabase_token>`, `Content-Type: application/json`
- **Body**:
```json
{
  "extracted_text": "Confirmed job description text with minimum 50 characters...",
  "job_title": "Senior Backend Engineer",
  "company_name": "Stripe"
}
```
- **Response**: Standard `JobResponse` object with extracted requirements persisted in Supabase.

---

## Known Limitations & Best Practices

1. **Multi-Column Reading Orders**: Standard multi-column layout flows may interleave paragraphs if margins are tight. The editable preview allows users to adjust paragraph order before analysis.
2. **Complex Embedded Tables**: Data in borderless multi-row tables may extract line-by-line rather than in column pairs. Users can review the extracted text preview.
3. **Extremely Low-Resolution Scans**: Scanned images below 100 DPI or heavily rotated pages may produce degraded OCR character accuracy. The system returns quality warnings when OCR character counts are low.
4. **Password-Protected Documents**: Protected or encrypted PDFs are rejected; users must upload unlocked documents.

---

## Running Automated Tests

The test suite includes **82 automated tests** covering SSRF safety, URL validation, tree filtering, secret sanitization, duplicate normalization, LLM parsing, unauthenticated access, skill normalization, deterministic scoring, gap prioritization, assessment persistence, commit diffing, idempotency keys, evidence reconciliation, reassessment versioning, ChromaDB RAG vector indexing, and PDF text extraction/OCR:

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -v
```

---

## Judge-Ready Live Demo Checklist (Phase 8 & 9)

1. **Sign In & Setup**:
   - Log into CareerProof AI at `http://localhost:5173`.
   - Navigate to **Job Analysis**.
2. **PDF Job Description Ingestion**:
   - Toggle to **Upload PDF (Digital & OCR)**.
   - Drag and drop or browse to select a job description PDF (digital or scanned).
   - Click **Extract Text from PDF**. Observe the page count, extraction method badge (`Digital Text`, `Full OCR`, or `Hybrid`), and editable text preview.
   - Make any desired edits in the preview textarea and click **Confirm and Analyze Job Description**.
3. **Structured Skill Extraction**:
   - View the extracted technical requirements categorized into Programming Languages, Frameworks, Deployment, Databases, and Core concepts.
4. **ChromaDB RAG Assessment**:
   - Go to **Skill Gaps** and select your analyzed job and GitHub repository.
   - Run the assessment: the RAG vector engine retrieves semantic code chunks from ChromaDB, audits evidence, and displays line-verified code excerpts with match scores.
5. **Continuous Commit Monitoring**:
   - Push a commit to your repository or click **Check Changes** in **Repository Activity** to see automated evidence reconciliation and version lineage (`v1` &rarr; `v2`).

