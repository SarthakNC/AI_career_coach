-- CareerProof AI — Phase 7: AI-Powered Skill-Gap Assessment Schema
-- Migration: phase7_skill_gap_analyzer.sql

-- 1. Create `assessments` table
CREATE TABLE IF NOT EXISTS public.assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    job_title TEXT,
    company_name TEXT,
    selected_repository_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    repositories_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'completed', -- 'pending' | 'completed' | 'failed'
    match_score NUMERIC(5, 2), -- 0.00 to 100.00 or NULL if no requirements
    scoring_method TEXT NOT NULL DEFAULT 'weighted_average_v1',
    total_requirements INT NOT NULL DEFAULT 0,
    demonstrated_count INT NOT NULL DEFAULT 0,
    partially_demonstrated_count INT NOT NULL DEFAULT 0,
    not_demonstrated_count INT NOT NULL DEFAULT 0,
    score_explanation JSONB DEFAULT '{}'::jsonb,
    assessment_limitations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    completed_at TIMESTAMPTZ
);

-- 2. Create `assessment_requirement_results` table
CREATE TABLE IF NOT EXISTS public.assessment_requirement_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES public.assessments(id) ON DELETE CASCADE,
    requirement_id UUID REFERENCES public.job_requirements(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    normalized_skill_name TEXT NOT NULL,
    category TEXT NOT NULL,
    importance TEXT NOT NULL DEFAULT 'required', -- 'required' | 'preferred'
    requirement_weight NUMERIC(3, 2) NOT NULL DEFAULT 1.0,
    status TEXT NOT NULL, -- 'demonstrated' | 'partially_demonstrated' | 'not_demonstrated'
    status_score NUMERIC(3, 2) NOT NULL DEFAULT 0.0, -- 1.0, 0.5, 0.0
    score_contribution NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    explanation TEXT NOT NULL,
    supporting_evidence_ids JSONB DEFAULT '[]'::jsonb,
    supporting_evidence JSONB DEFAULT '[]'::jsonb, -- immutable snapshot of matched evidence items
    limitations TEXT,
    suggested_next_step TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. Create `assessment_recommendations` table
CREATE TABLE IF NOT EXISTS public.assessment_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES public.assessments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    related_requirement_ids JSONB DEFAULT '[]'::jsonb,
    related_skills JSONB DEFAULT '[]'::jsonb,
    priority TEXT NOT NULL DEFAULT 'medium', -- 'high' | 'medium' | 'low'
    reason TEXT NOT NULL,
    suggested_task TEXT NOT NULL,
    expected_artifact TEXT NOT NULL,
    evidence_to_produce TEXT NOT NULL,
    related_repository_id UUID REFERENCES public.repositories(id) ON DELETE SET NULL,
    related_repository_name TEXT,
    estimated_effort TEXT,
    limitations TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Indexes for fast query lookup
CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON public.assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_job_id ON public.assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON public.assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessment_reqs_assessment ON public.assessment_requirement_results(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_reqs_user ON public.assessment_requirement_results(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_reqs_status ON public.assessment_requirement_results(status);
CREATE INDEX IF NOT EXISTS idx_assessment_recs_assessment ON public.assessment_recommendations(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_recs_user ON public.assessment_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_assessment_recs_priority ON public.assessment_recommendations(priority);

-- 5. Enable Row Level Security (RLS)
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_requirement_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_recommendations ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies for `assessments`
CREATE POLICY "Users can view their own assessments"
    ON public.assessments FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assessments"
    ON public.assessments FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assessments"
    ON public.assessments FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own assessments"
    ON public.assessments FOR DELETE USING (auth.uid() = user_id);

-- 7. RLS Policies for `assessment_requirement_results`
CREATE POLICY "Users can view their own assessment requirement results"
    ON public.assessment_requirement_results FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assessment requirement results"
    ON public.assessment_requirement_results FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assessment requirement results"
    ON public.assessment_requirement_results FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own assessment requirement results"
    ON public.assessment_requirement_results FOR DELETE USING (auth.uid() = user_id);

-- 8. RLS Policies for `assessment_recommendations`
CREATE POLICY "Users can view their own assessment recommendations"
    ON public.assessment_recommendations FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assessment recommendations"
    ON public.assessment_recommendations FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assessment recommendations"
    ON public.assessment_recommendations FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own assessment recommendations"
    ON public.assessment_recommendations FOR DELETE USING (auth.uid() = user_id);
