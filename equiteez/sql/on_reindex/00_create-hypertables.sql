-- `dipdup schema wipe` cannot drop these tables (TimescaleDB blocks
-- the cascade through continuous aggregates with dependent plain views)
-- and silently leaves them behind WITH their rows. Clear them before
-- hypertable conversion / cagg creation so stale data never gets
-- migrated into chunks or materialized. No-op on a clean database.
-- (Their FK constraints, also lost during the wipe, are restored in
-- 08_restore-foreign-keys.sql.)
TRUNCATE TABLE dodo_mav, dodo_mav_history_data, launchpad_purchase_event, orderbook_order_event CASCADE;

-- Create hypertable for equiteez_user_token_transfer
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'equiteez_user_token_transfer_pkey') THEN
        ALTER TABLE equiteez_user_token_transfer DROP CONSTRAINT equiteez_user_token_transfer_pkey;
    END IF;
    ALTER TABLE equiteez_user_token_transfer ADD PRIMARY KEY (id, timestamp);
END $$;

SELECT create_hypertable('equiteez_user_token_transfer', 'timestamp', 
                        chunk_time_interval => INTERVAL '1 day',
                        if_not_exists => TRUE);

-- Check if DodoMavHistoryData is already a hypertable
DO $$
DECLARE
    is_hypertable boolean;
BEGIN
    -- Check if table is already a hypertable
    SELECT EXISTS (
        SELECT 1
        FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'dodo_mav_history_data'
    ) INTO is_hypertable;

    -- Only proceed if not already a hypertable
    IF NOT is_hypertable THEN
        -- Drop existing primary key if it exists
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dodo_mav_history_data_pkey') THEN
            ALTER TABLE dodo_mav_history_data DROP CONSTRAINT dodo_mav_history_data_pkey;
        END IF;

        -- Add new primary key
        ALTER TABLE dodo_mav_history_data ADD PRIMARY KEY (id, timestamp);

        -- Create hypertable
        PERFORM create_hypertable('dodo_mav_history_data', 'timestamp',
                                chunk_time_interval => INTERVAL '1 day',
                                if_not_exists => TRUE,
                                migrate_data => TRUE);
    END IF;
END $$;

-- Launch purchases start from a clean ORM schema. Its unique key already
-- contains timestamp and the call coordinates, so it is valid for Timescale.
ALTER TABLE launchpad_purchase_event
    DROP CONSTRAINT launchpad_purchase_event_pkey,
    ADD PRIMARY KEY (id, timestamp),
    ADD CONSTRAINT launchpad_purchase_snapshot_naturals CHECK (
        (price IS NULL OR (price >= 0 AND price < 'Infinity'::numeric)) AND
        (total IS NULL OR (total >= 0 AND total < 'Infinity'::numeric))
    );

SELECT create_hypertable('launchpad_purchase_event', 'timestamp',
    chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);
