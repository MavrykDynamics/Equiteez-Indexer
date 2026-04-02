-- Migration: Create events_outbox table + failure-tracking
--
-- Stores domain events published to the Event Bus by a relayer. The outbox
-- pattern keeps domain writes and events in one transaction.
--
-- Failure-tracking columns let the relayer record per-row retry state so rows
-- that exceed max retries are skipped instead of retried forever.
--
-- Apply: psql $DATABASE_URL -f equiteez/sql/migrations/001_create_events_outbox.sql

CREATE TABLE IF NOT EXISTS events_outbox (
    id BIGSERIAL PRIMARY KEY,

    event_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    source VARCHAR(100) NOT NULL DEFAULT 'dipdup-indexer',
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,

    payload JSONB NOT NULL,

    published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NULL,
    failed_at TIMESTAMP WITH TIME ZONE NULL,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Existing deployments created before failure-tracking: add missing columns.
ALTER TABLE events_outbox
    ADD COLUMN IF NOT EXISTS retry_count int         NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error  text,
    ADD COLUMN IF NOT EXISTS failed_at   timestamptz;

-- Relayer: WHERE published = false AND retry_count < N. Replaces legacy
-- idx on (published, created_at) if present.
DROP INDEX IF EXISTS idx_events_outbox_unpublished;

CREATE INDEX IF NOT EXISTS idx_events_outbox_unpublished
    ON events_outbox (id)
    WHERE published = false;

CREATE INDEX IF NOT EXISTS idx_events_outbox_event_id
    ON events_outbox (event_id);

CREATE INDEX IF NOT EXISTS idx_events_outbox_aggregate
    ON events_outbox (aggregate_type, aggregate_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_outbox_event_type
    ON events_outbox (event_type, occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_outbox_payload
    ON events_outbox USING GIN (payload);

CREATE OR REPLACE FUNCTION update_events_outbox_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_events_outbox_updated_at
    BEFORE UPDATE ON events_outbox
    FOR EACH ROW
    EXECUTE FUNCTION update_events_outbox_updated_at();
