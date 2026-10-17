-- Parivartan AI — Phase 6: AI-Powered GitHub Portfolio Analyzer Schema
-- Migration: phase6_github_analyzer.sql

-- 1. Create `repositories` table
CREATE TABLE IF NOT EXISTS public.repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    github_id BIGINT,
    full_name TEXT NOT NULL,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    description TEXT,
    html_url TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    language TEXT,
    languages_breakdown JSONB DEFAULT '{}'::jsonb,
    stargazers_count INT DEFAULT 0,
    forks_count INT DEFAULT 0,
    open_issues_count INT DEFAULT 0,
    is_fork BOOLEAN DEFAULT FALSE,
    is_private BOOLEAN DEFAULT FALSE,
    latest_commit_sha TEXT,
    last_analyzed_commit_sha TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_user_repository UNIQUE (user_id, full_name)
);

-- 2. Create `analysis_runs` table
CREATE TABLE IF NOT EXISTS public.analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    commit_sha TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'running' | 'completed' | 'failed'
    total_files_discovered INT DEFAULT 0,
    files_analyzed_count INT DEFAULT 0,
    evidence_count INT DEFAULT 0,
    project_insights JSONB DEFAULT '{}'::jsonb,
    error_summary TEXT,
    analysis_limitations TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Create `skill_evidence` table
CREATE TABLE IF NOT EXISTS public.skill_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES public.analysis_runs(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL,
    evidence_type TEXT NOT NULL, -- 'source_code' | 'test' | 'configuration' | 'dependency' | 'documentation'
    status_label TEXT NOT NULL DEFAULT 'Strong evidence', -- 'Strong evidence' | 'Some evidence' | 'Mentioned only' | 'Not demonstrated in analyzed files'
    evidence_summary TEXT NOT NULL,
    file_path TEXT,
    line_start INT,
    line_end INT,
    code_excerpt TEXT,
    github_url TEXT,
    commit_sha TEXT NOT NULL,
    confidence NUMERIC(3, 2) DEFAULT 0.85, -- 0.00 to 1.00
    limitations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Indexes for fast query lookup
CREATE INDEX IF NOT EXISTS idx_repositories_user_id ON public.repositories(user_id);
CREATE INDEX IF NOT EXISTS idx_repositories_updated_at ON public.repositories(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_repo ON public.analysis_runs(repository_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_user ON public.analysis_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_evidence_run ON public.skill_evidence(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_skill_evidence_repo ON public.skill_evidence(repository_id);
CREATE INDEX IF NOT EXISTS idx_skill_evidence_user ON public.skill_evidence(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_evidence_skill ON public.skill_evidence(skill_name);

-- 5. Enable Row Level Security (RLS)
ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_evidence ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies for `repositories`
CREATE POLICY "Users can view their own repositories"
    ON public.repositories FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own repositories"
    ON public.repositories FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own repositories"
    ON public.repositories FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own repositories"
    ON public.repositories FOR DELETE USING (auth.uid() = user_id);

-- 7. RLS Policies for `analysis_runs`
CREATE POLICY "Users can view their own analysis runs"
    ON public.analysis_runs FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analysis runs"
    ON public.analysis_runs FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analysis runs"
    ON public.analysis_runs FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analysis runs"
    ON public.analysis_runs FOR DELETE USING (auth.uid() = user_id);

-- 8. RLS Policies for `skill_evidence`
CREATE POLICY "Users can view their own skill evidence"
    ON public.skill_evidence FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own skill evidence"
    ON public.skill_evidence FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own skill evidence"
    ON public.skill_evidence FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own skill evidence"
    ON public.skill_evidence FOR DELETE USING (auth.uid() = user_id);
