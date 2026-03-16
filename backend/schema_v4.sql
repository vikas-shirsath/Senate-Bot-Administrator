-- ═══════════════════════════════════════════════════════════
-- Schema v4 — Admin role support
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════

-- 1) Add role column (default 'user')
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- ── HARDCODED ADMIN ACCOUNT ─────────────────────────────────
-- Email:    admin@senate.gov
-- Password: Admin@123456
--
-- Step 1: Create the auth user in Supabase Authentication
--   Go to Supabase Dashboard → Authentication → Users → Add User
--   Email: admin@senate.gov  Password: Admin@123456
--
-- Step 2: After creating the auth user, copy the UUID and run:
--   (Replace <ADMIN_UUID> with the real UUID from auth.users)

-- INSERT INTO users (id, email, name, role)
-- VALUES (
--   '<ADMIN_UUID>',
--   'admin@senate.gov',
--   'Senate Admin',
--   'admin'
-- )
-- ON CONFLICT (id) DO UPDATE SET role = 'admin';

-- ── Alternatively — set any existing user as admin ──────────
-- UPDATE users SET role = 'admin' WHERE email = 'admin@senate.gov';

-- ── Or promote your own account to admin ────────────────────
-- UPDATE users SET role = 'admin' WHERE email = 'YOUR_EMAIL_HERE';
