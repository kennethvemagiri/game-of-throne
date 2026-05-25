-- Game of Throne — Supabase schema
-- Run this in Supabase SQL Editor (supabase.com → project → SQL Editor)

-- Applications table (replaces applications.json)
CREATE TABLE applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email_id TEXT UNIQUE,
    company TEXT,
    role TEXT,
    status TEXT NOT NULL DEFAULT 'needs_review',
    suggested_status TEXT,
    confidence TEXT,
    subject TEXT,
    snippet TEXT,
    received_at TIMESTAMPTZ,
    classified_at TIMESTAMPTZ,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Suggested jobs table (replaces suggested_jobs.json)
CREATE TABLE suggested_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source TEXT DEFAULT 'indeed',
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT,
    status TEXT DEFAULT 'pending',
    suggested_at TIMESTAMPTZ DEFAULT NOW(),
    viewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Gmail sync metadata (replaces last_fetch.json)
CREATE TABLE sync_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_email_id ON applications(email_id);
CREATE INDEX idx_suggested_jobs_status ON suggested_jobs(status);
