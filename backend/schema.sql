-- ═══════════════════════════════════════════════════════════
-- Senate Bot Administrator — Supabase Database Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ═══════════════════════════════════════════════════════════

-- ── 1. Users table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own row"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own row"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own row"
    ON users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ── 2. Chats table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chats_user_id ON chats(user_id);

ALTER TABLE chats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own chats"
    ON chats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own chats"
    ON chats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chats"
    ON chats FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own chats"
    ON chats FOR DELETE
    USING (auth.uid() = user_id);

-- ── 3. Messages table ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_chat_id ON messages(chat_id);

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read messages of own chats"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM chats WHERE chats.id = messages.chat_id AND chats.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert messages to own chats"
    ON messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM chats WHERE chats.id = messages.chat_id AND chats.user_id = auth.uid()
        )
    );

-- ── 4. Service Requests table ──────────────────────────────
CREATE TABLE IF NOT EXISTS service_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL,
    request_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_service_requests_user_id ON service_requests(user_id);
CREATE INDEX idx_service_requests_request_id ON service_requests(request_id);

ALTER TABLE service_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own service requests"
    ON service_requests FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own service requests"
    ON service_requests FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ── 5. Service role bypass (for backend using SERVICE_KEY) ──
-- The service role key bypasses RLS by default in Supabase,
-- so the backend can read/write all rows when needed.
