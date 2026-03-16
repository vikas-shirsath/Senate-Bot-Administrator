-- ═══════════════════════════════════════════════════════════
-- Schema v5 — Certificate Tables & Generic File Storage
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════

-- Permit Certificates
CREATE TABLE IF NOT EXISTS permit_certificates (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    issue_number TEXT NOT NULL,
    permit_number TEXT UNIQUE NOT NULL,
    owner TEXT NOT NULL,
    business TEXT NOT NULL,
    address TEXT NOT NULL,
    activity TEXT NOT NULL,
    authority TEXT DEFAULT 'Government of Maharashtra',
    start_date TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    city TEXT NOT NULL,
    issued_date TEXT NOT NULL,
    aadhaar_document_url TEXT DEFAULT '',
    pan_document_url TEXT DEFAULT '',
    certificate_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Income Certificates
CREATE TABLE IF NOT EXISTS income_certificates (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    certificate_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    village TEXT NOT NULL,
    taluka TEXT NOT NULL,
    district TEXT NOT NULL,
    financial_year TEXT NOT NULL,
    annual_income TEXT NOT NULL,
    income_words TEXT NOT NULL,
    place TEXT NOT NULL,
    date TEXT NOT NULL,
    aadhaar_document_url TEXT DEFAULT '',
    pan_document_url TEXT DEFAULT '',
    certificate_url TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enhance generic service_requests table for file uploads
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS attached_file_urls TEXT[] DEFAULT '{}';

-- Enable RLS but allow service key full access
ALTER TABLE permit_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE income_certificates ENABLE ROW LEVEL SECURITY;

-- Users can read their own certificates
DO $$ BEGIN
    CREATE POLICY "Users read own permits" ON permit_certificates FOR SELECT USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE POLICY "Users read own income certs" ON income_certificates FOR SELECT USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
