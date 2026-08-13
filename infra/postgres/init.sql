CREATE TABLE IF NOT EXISTS platform_health (
    id BIGSERIAL PRIMARY KEY,
    component TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
