# CareerProof AI

> **Agentic AI platform comparing a student's verified GitHub portfolio evidence against real-world job & internship requirements.**

CareerProof AI bridges the gap between traditional resumes and actual software engineering skill evidence. Rather than relying on self-reported keywords, CareerProof AI extracts evidence-grounded skills directly from real GitHub commits and compares them to parsed job descriptions.

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
       └── /api/v1/github/...             ──> [GitHub REST API + Bounded Tree Ingestion]
                                                        │
                                                        ▼
                                          [LLM Architecture & Skill Reasoner]
                                                        │
                                                        ▼
                                          [Supabase PostgreSQL (PostgREST + RLS)]
                                          ├── public.jobs
                                          ├── public.job_requirements
                                          ├── public.repositories
                                          ├── public.analysis_runs
                                          └── public.skill_evidence
```

---

## Phase 6 Capabilities

1. **GitHub Discovery & Resolution**: Resolve GitHub usernames or public repository URLs to discover repositories, branches, languages, and latest commit SHAs.
2. **Commit-Bound File Selection**: Recursive git tree extraction prioritized by high-signal files (manifests, route definitions, schemas, tests, configurations, and core code) while strictly excluding binaries, lockfiles, and `node_modules`.
3. **Secret Redaction**: Automatic pre-scanning and redaction of probable API keys, personal access tokens, and JWTs prior to LLM reasoning.
4. **Evidence-Grounded Skill Detection**: Identifies skills with transparent status labels (`Strong evidence`, `Some evidence`, `Mentioned only`), file paths, line ranges, and verified code excerpts from genuine file contents.
5. **Project Quality & Architecture Insights**:
   - Observed technology stack (direct implementation vs. dependency mention).
   - Component architecture overview & text-based flow diagram.
   - Engineering practices (validation, error handling, testing, CI/CD).
   - Project strengths & prioritized improvement recommendations.
   - Analysis coverage transparency & declared static analysis limitations.
6. **Database Persistence & RLS**: All repositories, runs, and skill evidence are saved in Supabase PostgreSQL under Row Level Security. Reloading the page immediately restores previously analyzed projects.

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

## Supabase Database Setup

Run the SQL migration scripts in your **Supabase Dashboard > SQL Editor**:

1. **Phase 5 Schema**: [`backend/migrations/phase5_job_analyzer.sql`](backend/migrations/phase5_job_analyzer.sql)
   - Creates `jobs` and `job_requirements` tables with RLS.
2. **Phase 6 Schema**: [`backend/migrations/phase6_github_analyzer.sql`](backend/migrations/phase6_github_analyzer.sql)
   - Creates `repositories`, `analysis_runs`, and `skill_evidence` tables with RLS and cascading deletion.

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

## Running the Automated Test Suite

The test suite includes 26 automated tests covering SSRF safety, URL validation, tree filtering, secret sanitization, duplicate normalization, LLM parsing, unauthenticated access, and cross-user data isolation:

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -v
```

---

## Judge-Ready Demo Checklist (Phase 6)

1. **Sign In**: Log into CareerProof AI using an email/password account.
2. **Navigate to GitHub Portfolio**: Click on **GitHub Portfolio** in the sidebar.
3. **Import a Repository**:
   - Click **Add Repository**.
   - Enter a public GitHub repository URL (e.g. `https://github.com/octocat/Hello-World` or any public project) or a GitHub username.
   - Click **Resolve** and then **Add to Portfolio**.
4. **Analyze the Project**:
   - In the repository list, click **Analyze Repository**.
   - Watch the bounded analyzer fetch the tree at the target commit, select high-signal files, and extract evidence.
5. **Inspect Skill Evidence**:
   - Explore skills categorized by domain.
   - Click the expand toggle on any skill card to review the verified file reference, line range, and actual source code excerpt.
   - Click **View on GitHub** to jump directly to the verified commit and line on GitHub.
6. **Inspect Project Insights**:
   - Switch to the **Project Quality & Architecture** tab.
   - Review the observed tech stack, system architecture summary, engineering practices, strengths, and prioritized improvement opportunities.
   - Review **Coverage & Limitations** to inspect file discovery metrics and transparent static inspection boundaries.
7. **Verify Persistence**:
   - Refresh the browser (`F5`).
   - Notice the repository and its full analysis run load from Supabase PostgreSQL.
