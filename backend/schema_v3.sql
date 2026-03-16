-- ═══════════════════════════════════════════════════════════
-- Senate Bot Administrator — Schema Migration v3
-- Run this in Supabase SQL Editor AFTER schema_v2.sql
-- Adds multilingual + voice columns to messages table
-- ═══════════════════════════════════════════════════════════

-- New columns for multilingual and voice support
ALTER TABLE messages ADD COLUMN IF NOT EXISTS input_type TEXT DEFAULT 'text';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS original_language TEXT DEFAULT 'en';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS original_text TEXT DEFAULT '';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS translated_english TEXT DEFAULT '';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS response_english TEXT DEFAULT '';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS response_hindi TEXT DEFAULT '';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS response_marathi TEXT DEFAULT '';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS audio_url TEXT DEFAULT '';
