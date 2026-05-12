-- ================================================================
-- SearchLight Supabase 스키마
-- 사용법: Supabase 콘솔 → SQL Editor에 전체 붙여넣고 실행
-- ================================================================


-- ----------------------------------------------------------------
-- 0. 기존 테이블/타입 전체 삭제 (외래키 의존 순서 주의)
-- ----------------------------------------------------------------
DROP TABLE IF EXISTS cropped_objects  CASCADE;
DROP TABLE IF EXISTS event_clips      CASCADE;
DROP TABLE IF EXISTS event_intents    CASCADE;
DROP TABLE IF EXISTS event            CASCADE;
DROP TABLE IF EXISTS normal           CASCADE;
DROP TABLE IF EXISTS processing_log   CASCADE;
DROP TABLE IF EXISTS search_logs      CASCADE;
DROP TYPE  IF EXISTS situation_type   CASCADE;


-- ----------------------------------------------------------------
-- 1. ENUM
-- ----------------------------------------------------------------
CREATE TYPE situation_type AS ENUM (
    'falling',   -- 낙상
    'break',     -- 기물 파손
    'assault',   -- 폭행
    'theft',     -- 절도
    'smoking',   -- 흡연
    'disaster'   -- 재난
);


-- ----------------------------------------------------------------
-- 2. 테이블
-- ----------------------------------------------------------------

-- 정상 영상 기록
CREATE TABLE normal (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    video_filename  TEXT        NOT NULL,
    timestamp       TIMESTAMPTZ,
    summary         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 이상 이벤트 (핵심 테이블)
CREATE TABLE event (
    id              UUID            DEFAULT gen_random_uuid() PRIMARY KEY,
    video_filename  TEXT            NOT NULL,
    timestamp       TIMESTAMPTZ,
    summary         TEXT,
    short_summary   TEXT,
    count_people    INT             DEFAULT 0,
    situation       situation_type,
    clip_url        TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- 이벤트 의도별 문장 (벡터 검색용)
CREATE TABLE event_intents (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id    UUID        REFERENCES event(id) ON DELETE CASCADE,
    time_sent   TEXT,
    count_sent  TEXT,
    action_sent TEXT,
    info_sent   TEXT,
    error_sent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 이벤트 영상 클립 (이벤트당 여러 클립 지원)
CREATE TABLE event_clips (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id    UUID        REFERENCES event(id) ON DELETE CASCADE,
    clip_url    TEXT,
    start_sec   NUMERIC,
    end_sec     NUMERIC,
    clip_index  INT         DEFAULT 1,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 영상 처리 로그
CREATE TABLE processing_log (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    video_filename  TEXT        NOT NULL,
    model_type      TEXT,
    status          TEXT        NOT NULL,
    situation       TEXT,
    frame_count     INT         DEFAULT 0,
    motion_count    INT         DEFAULT 0,
    max_people      INT         DEFAULT 0,
    clip_count      INT         DEFAULT 0,
    error_message   TEXT,
    duration_sec    NUMERIC,
    processed_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 크롭 객체 이미지 (CLIP 벡터 검색용)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE cropped_objects (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id        UUID        REFERENCES event(id) ON DELETE CASCADE,
    video_filename  TEXT        NOT NULL,
    timestamp       TIMESTAMPTZ,
    object_class    TEXT,
    bbox            JSONB,
    image_url       TEXT,
    clip_vector     vector(512),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 사용자 검색 기록 + AI 보고서
CREATE TABLE search_logs (
    id               BIGSERIAL   PRIMARY KEY,
    query            TEXT        NOT NULL,
    intent           TEXT,
    session_id       TEXT        DEFAULT 'default',
    ai_report        TEXT,
    results          TEXT,
    feedback         TEXT,
    feedback_comment TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);


-- ----------------------------------------------------------------
-- 3. 인덱스
-- ----------------------------------------------------------------
CREATE INDEX idx_normal_timestamp       ON normal(timestamp DESC);
CREATE INDEX idx_event_timestamp        ON event(timestamp DESC);
CREATE INDEX idx_event_situation        ON event(situation);
CREATE INDEX idx_event_intents_event    ON event_intents(event_id);
CREATE INDEX idx_event_clips_event      ON event_clips(event_id);
CREATE INDEX idx_processing_log_video   ON processing_log(video_filename);
CREATE INDEX idx_processing_log_status  ON processing_log(status);
CREATE INDEX idx_processing_log_time    ON processing_log(processed_at DESC);
CREATE INDEX idx_cropped_objects_event  ON cropped_objects(event_id);
CREATE INDEX idx_cropped_objects_class  ON cropped_objects(object_class);
CREATE INDEX idx_search_logs_session    ON search_logs(session_id);
CREATE INDEX idx_search_logs_time       ON search_logs(created_at DESC);


-- ----------------------------------------------------------------
-- 4. RPC 함수 — CLIP 벡터 유사도 검색
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_cropped_objects(
    query_embedding  vector(512),
    match_threshold  float,
    match_count      int
)
RETURNS TABLE (
    id             uuid,
    event_id       uuid,
    video_filename text,
    "timestamp"    timestamptz,
    object_class   text,
    bbox           jsonb,
    image_url      text,
    similarity     float
)
LANGUAGE sql STABLE AS $$
    SELECT id, event_id, video_filename, timestamp, object_class, bbox, image_url,
           1 - (clip_vector <=> query_embedding) AS similarity
    FROM   cropped_objects
    WHERE  clip_vector IS NOT NULL
      AND  1 - (clip_vector <=> query_embedding) > match_threshold
    ORDER  BY clip_vector <=> query_embedding
    LIMIT  match_count;
$$;


-- ----------------------------------------------------------------
-- 5. Storage 버킷
-- ----------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public)
VALUES ('cctv-clips', 'cctv-clips', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('cctv-crops', 'cctv-crops', true)
ON CONFLICT (id) DO NOTHING;
