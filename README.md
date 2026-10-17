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

## Supabase Database Migrations

Run each migration script in your **Supabase Dashboard > SQL Editor**:

1. **Phase 5 Schema**: [`backend/migrations/phase5_job_analyzer.sql`](backend/migrations/phase5_job_analyzer.sql)
   - Creates `jobs` and `job_requirements` tables with RLS.
2. **Phase 6 Schema**: [`backend/migrations/phase6_github_analyzer.sql`](backend/migrations/phase6_github_analyzer.sql)
   - Creates `repositories`, `analysis_runs`, and `skill_evidence` tables with RLS and cascading deletion.
3. **Phase 7 Schema**: [`backend/migrations/phase7_skill_gap_analyzer.sql`](backend/migrations/phase7_skill_gap_analyzer.sql)
   - Creates `assessments`, `assessment_requirement_results`, and `assessment_recommendations` tables with indexes, foreign keys, and RLS policies.

---

## Environment Variables

### Backend Configuration (`backend/.env`):
```env
# Supabase PostgreSQL Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_publishable_anon_key

# Optional: GitHub Personal Access Token (for higher rate limits)
GITHUB_TOKEN=your_github_token_optional

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

## Local Development Commands

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

### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

The test suite includes 46 automated tests covering SSRF safety, URL validation, tree filtering, secret sanitization, duplicate normalization, LLM parsing, unauthenticated access, skill normalization, deterministic scoring, gap prioritization, and assessment persistence:

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -v
```

---

## Judge-Ready Live Demo Checklist (Phase 7)

1. **Sign In**:
   - Log into CareerProof AI at `http://localhost:5173` with your authenticated account.
2. **Phase 5 Job Verification**:
   - Open **Job Analysis** in the sidebar.
   - Confirm a target job posting is analyzed (or paste a job description such as "Full Stack Python / React Developer").
3. **Phase 6 Portfolio Verification**:
   - Open **GitHub Portfolio** in the sidebar.
   - Confirm you have at least one repository imported and analyzed with verified skill evidence.
4. **Navigate to Skill-Gap Assessment**:
   - Click on **Skill Gaps** in the sidebar (or click the card on the dashboard).
5. **Configure & Start Assessment**:
   - **Step 1**: Select your analyzed target job. Notice the extracted requirements count.
   - **Step 2**: Select one or more analyzed repositories. Notice the verified evidence counts and commit SHAs.
   - Click **Start Skill-Gap Assessment**.
6. **Review Portfolio Match Score**:
   - Review the large, color-coded **Portfolio Evidence Match Score** (e.g. 75.0%).
   - Click **View Scoring Methodology** to review the transparent weighted-average formula and parameters.
7. **Inspect Requirements & Evidence**:
   - Filter requirements by status (**Demonstrated**, **Partially Demonstrated**, **Not Demonstrated in Analyzed Files**) or category.
   - Click **Inspect Evidence** on any requirement to open the **Evidence Detail Inspector**.
   - Review the verified source file path, line numbers, code excerpt, and the clickable **View on GitHub** link to the exact analyzed commit.
8. **Explore Prioritized Skill Gaps**:
   - Switch to the **Prioritized Gaps** tab.
   - Notice gaps ranked deterministically with required skills and unverified skills ranked first.
   - Review why evidence is insufficient, existing partial mentions, and the expected portfolio artifact.
9. **Review Personalized Action Plan**:
   - Switch to the **Action Plan** tab.
   - Review actionable, grounded recommendations targeting your existing repositories with estimated effort and concrete tasks.
10. **Verify Persistence & History**:
    - Click **History** in the top tab bar.
    - Notice your saved assessment listed with score, timestamp, and skill breakdown.
    - Click on the assessment item or refresh the page: observe that the entire assessment, code snapshots, and recommendations reload instantly without recomputation.
