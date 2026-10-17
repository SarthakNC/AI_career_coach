-- CareerProof AI — Phase 5: Job Requirement Analyzer Schema
-- Migration: phase5_job_analyzer.sql

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create `jobs` table
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_title TEXT,
    company_name TEXT,
    source_url TEXT,
    description TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Create `job_requirements` table
CREATE TABLE IF NOT EXISTS public.job_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL,
    importance TEXT NOT NULL DEFAULT 'required',
    description TEXT,
    source_excerpt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Indexes for fast query lookup & foreign keys
CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON public.jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON public.jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_requirements_job_id ON public.job_requirements(job_id);
CREATE INDEX IF NOT EXISTS idx_job_requirements_category ON public.job_requirements(category);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_requirements ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies for `jobs`
-- Users can view their own jobs
CREATE POLICY "Users can view their own jobs"
    ON public.jobs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own jobs
CREATE POLICY "Users can insert their own jobs"
    ON public.jobs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own jobs
CREATE POLICY "Users can update their own jobs"
    ON public.jobs
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own jobs
CREATE POLICY "Users can delete their own jobs"
    ON public.jobs
    FOR DELETE
    USING (auth.uid() = user_id);

-- 6. RLS Policies for `job_requirements`
-- Users can view requirements of jobs they own
CREATE POLICY "Users can view requirements of their own jobs"
    ON public.job_requirements
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.jobs
            WHERE public.jobs.id = public.job_requirements.job_id
              AND public.jobs.user_id = auth.uid()
        )
    );

-- Users can insert requirements for their own jobs
CREATE POLICY "Users can insert requirements for their own jobs"
    ON public.job_requirements
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.jobs
            WHERE public.jobs.id = public.job_requirements.job_id
              AND public.jobs.user_id = auth.uid()
        )
    );

-- Users can update requirements for their own jobs
CREATE POLICY "Users can update requirements for their own jobs"
    ON public.job_requirements
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.jobs
            WHERE public.jobs.id = public.job_requirements.job_id
              AND public.jobs.user_id = auth.uid()
        )
    );

-- Users can delete requirements for their own jobs
CREATE POLICY "Users can delete requirements for their own jobs"
    ON public.job_requirements
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.jobs
            WHERE public.jobs.id = public.job_requirements.job_id
              AND public.jobs.user_id = auth.uid()
        )
    );
