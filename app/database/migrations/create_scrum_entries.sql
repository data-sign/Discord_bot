-- Create scrum entries table
CREATE TABLE IF NOT EXISTS scrum_entries (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    yesterday_work TEXT NOT NULL,
    today_plan TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    message_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    is_edited BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scrum_entries_user_id ON scrum_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_scrum_entries_message_id ON scrum_entries(message_id);

-- Add table comment
COMMENT ON TABLE scrum_entries IS '디스코드 스크럼 인증 데이터';

-- RLS 정책 설정

-- Enable RLS
ALTER TABLE IF EXISTS scrum_entries ENABLE ROW LEVEL SECURITY;


-- 읽기 정책
CREATE POLICY "anon_read_policy" ON scrum_entries
    FOR SELECT
    TO anon
    USING (true);

-- 생성 정책
CREATE POLICY "anon_insert_policy" ON scrum_entries
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- 수정 정책
CREATE POLICY "anon_update_policy" ON scrum_entries
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);