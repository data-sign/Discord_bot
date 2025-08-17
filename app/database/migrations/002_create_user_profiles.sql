-- Create user profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    monthly_goal TEXT,
    weekly_goal TEXT,
    routine TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- Add table comment
COMMENT ON TABLE user_profiles IS '디스코드 유저 프로필 데이터';

-- Enable RLS
ALTER TABLE IF EXISTS user_profiles ENABLE ROW LEVEL SECURITY;

-- 읽기 정책
CREATE POLICY "anon_read_policy" ON user_profiles
    FOR SELECT
    TO anon
    USING (true);

-- 생성 정책
CREATE POLICY "anon_insert_policy" ON user_profiles
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- 수정 정책
CREATE POLICY "anon_update_policy" ON user_profiles
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);