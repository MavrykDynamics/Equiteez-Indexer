-- Lives in on_restart on purpose: dipdup creates a missing table on every start
-- but fires on_reindex only for a fresh schema, so on the no-wipe path this is the
-- only hook that can convert it. No cagg depends on it, so converting late is safe.
DO $$
DECLARE
    is_hypertable boolean;
    primary_key_name text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM timescaledb_information.hypertables
        WHERE hypertable_schema = current_schema()
          AND hypertable_name = 'orderbook_order_event'
    ) INTO is_hypertable;

    IF NOT is_hypertable THEN
        SELECT conname INTO primary_key_name
        FROM pg_constraint
        WHERE conrelid = 'orderbook_order_event'::regclass AND contype = 'p';
        IF primary_key_name IS NOT NULL THEN
            EXECUTE format('ALTER TABLE orderbook_order_event DROP CONSTRAINT %I', primary_key_name);
        END IF;

        ALTER TABLE orderbook_order_event
            ADD PRIMARY KEY (id, timestamp);

        PERFORM create_hypertable('orderbook_order_event', 'timestamp',
            chunk_time_interval => INTERVAL '30 days',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    END IF;
END $$;
