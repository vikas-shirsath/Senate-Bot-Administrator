-- ═══════════════════════════════════════════════════════════
-- Senate Bot Administrator — Schema Migration v2
-- Run this in Supabase SQL Editor AFTER the initial schema.sql
-- Adds applicant_details column and ration_cards / birth_certificates tables
-- ═══════════════════════════════════════════════════════════

-- Add applicant_details JSONB to service_requests for storing form data
ALTER TABLE service_requests
ADD COLUMN IF NOT EXISTS applicant_details JSONB DEFAULT '{}';

-- ── Ration Cards table ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS ration_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ration_id TEXT UNIQUE NOT NULL,
    holder_name TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    card_type TEXT DEFAULT 'BPL',
    entitlement TEXT DEFAULT '',
    scheme TEXT DEFAULT 'National Food Security Act',
    family_members INT DEFAULT 1,
    district TEXT DEFAULT '',
    state TEXT DEFAULT '',
    policy_reference TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ration_cards_user_id ON ration_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_ration_cards_ration_id ON ration_cards(ration_id);

ALTER TABLE ration_cards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own ration cards"
    ON ration_cards FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own ration cards"
    ON ration_cards FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ── Birth Certificates table ───────────────────────────────
CREATE TABLE IF NOT EXISTS birth_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'Processing',
    issue_date DATE,
    district TEXT DEFAULT '',
    state TEXT DEFAULT '',
    date_of_birth DATE,
    father_name TEXT DEFAULT '',
    mother_name TEXT DEFAULT '',
    place_of_birth TEXT DEFAULT '',
    policy_reference TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_birth_certs_user_id ON birth_certificates(user_id);
CREATE INDEX IF NOT EXISTS idx_birth_certs_cert_id ON birth_certificates(certificate_id);

ALTER TABLE birth_certificates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own birth certificates"
    ON birth_certificates FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own birth certificates"
    ON birth_certificates FOR INSERT
    WITH CHECK (auth.uid() = user_id);
