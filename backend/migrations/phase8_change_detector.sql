-- Parivartan AI — Phase 8: Automatic GitHub Change Detection & AI Career Reassessment
-- Migration: phase8_change_detector.sql

-- 1. Create `github_change_events` table for durable change processing
CREATE TABLE IF NOT EXISTS public.github_change_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    repository_name TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE, -- '{repository_id}:{detected_commit_sha}'
    previous_commit_sha TEXT,
    detected_commit_sha TEXT NOT NULL,
    commit_message TEXT,
    commit_author TEXT,
    commit_timestamp TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'
    changed_files JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{filename, status, additions, deletions}]
    changed_files_count INT NOT NULL DEFAULT 0,
    evidence_updated BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_change_summary JSONB DEFAULT '{}'::jsonb, -- {added_count, updated_count, invalidated_count, skills_affected}
    assessments_recalculated_count INT NOT NULL DEFAULT 0,
    assessment_updates JSONB DEFAULT '[]'::jsonb, -- [{assessment_id, job_title, previous_score, new_score, score_delta, new_version}]
    processing_attempts INT NOT NULL DEFAULT 0,
    last_error TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. Extend `public.assessments` for versioning and reassessment lineage
ALTER TABLE public.assessments ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1;
ALTER TABLE public.assessments ADD COLUMN IF NOT EXISTS parent_assessment_id UUID REFERENCES public.assessments(id) ON DELETE SET NULL;
ALTER TABLE public.assessments ADD COLUMN IF NOT EXISTS trigger_event_id UUID REFERENCES public.github_change_events(id) ON DELETE SET NULL;
ALTER TABLE public.assessments ADD COLUMN IF NOT EXISTS trigger_commit_sha TEXT;
ALTER TABLE public.assessments ADD COLUMN IF NOT EXISTS score_delta NUMERIC(5, 2) DEFAULT 0.0;

-- 3. Extend `public.repositories` for monitoring metadata
ALTER TABLE public.repositories ADD COLUMN IF NOT EXISTS monitoring_enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE public.repositories ADD COLUMN IF NOT EXISTS last_polled_at TIMESTAMPTZ;
ALTER TABLE public.repositories ADD COLUMN IF NOT EXISTS last_poll_status TEXT DEFAULT 'ok'; -- 'ok' | 'error' | 'rate_limited'

-- 4. Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_change_events_user_id ON public.github_change_events(user_id);
CREATE INDEX IF NOT EXISTS idx_change_events_repo_id ON public.github_change_events(repository_id);
CREATE INDEX IF NOT EXISTS idx_change_events_status ON public.github_change_events(status);
CREATE INDEX IF NOT EXISTS idx_change_events_detected_at ON public.github_change_events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_parent ON public.assessments(parent_assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessments_trigger_event ON public.assessments(trigger_event_id);

-- 5. Enable Row Level Security (RLS) on `github_change_events`
ALTER TABLE public.github_change_events ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies for `github_change_events`
CREATE POLICY "Users can view their own change events"
    ON public.github_change_events FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own change events"
    ON public.github_change_events FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own change events"
    ON public.github_change_events FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own change events"
    ON public.github_change_events FOR DELETE USING (auth.uid() = user_id);
