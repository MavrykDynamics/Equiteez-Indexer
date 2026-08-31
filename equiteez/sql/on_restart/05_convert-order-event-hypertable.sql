DO $$
DECLARE
    is_hypertable boolean;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'orderbook_order_event'
    ) INTO is_hypertable;

    IF NOT is_hypertable THEN
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'orderbook_order_event_pkey') THEN
            ALTER TABLE orderbook_order_event DROP CONSTRAINT orderbook_order_event_pkey;
        END IF;

        ALTER TABLE orderbook_order_event
            ADD PRIMARY KEY (id, timestamp);

        PERFORM create_hypertable('orderbook_order_event', 'timestamp',
            chunk_time_interval => INTERVAL '30 days',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    END IF;
END $$;
