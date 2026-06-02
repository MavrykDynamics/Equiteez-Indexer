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

-- Convert launchpad_purchase_event to a hypertable for continuous aggregates.
DO $$
DECLARE
    is_hypertable boolean;
    dedup_constraint_name text;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'launchpad_purchase_event'
    ) INTO is_hypertable;

    IF NOT is_hypertable THEN
        -- Backfill batch_index column if missing (Phase 1 #2 migration)
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'launchpad_purchase_event' AND column_name = 'batch_index'
        ) THEN
            ALTER TABLE launchpad_purchase_event
                ADD COLUMN batch_index integer NOT NULL DEFAULT 0;
        END IF;

        -- Drop the Tortoise-managed PK on id alone
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'launchpad_purchase_event_pkey') THEN
            ALTER TABLE launchpad_purchase_event DROP CONSTRAINT launchpad_purchase_event_pkey;
        END IF;

        -- Drop any existing dedup unique constraint by column count (Tortoise
        -- auto-names; this also catches old 6-column versions from Phase 1).
        FOR dedup_constraint_name IN
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'launchpad_purchase_event'::regclass AND contype = 'u'
        LOOP
            EXECUTE format('ALTER TABLE launchpad_purchase_event DROP CONSTRAINT %I', dedup_constraint_name);
        END LOOP;

        -- Composite PK including timestamp (required by Timescale)
        ALTER TABLE launchpad_purchase_event
            ADD PRIMARY KEY (id, timestamp);

        -- Replay-dedup constraint extended with timestamp
        ALTER TABLE launchpad_purchase_event
            ADD CONSTRAINT launchpad_purchase_event_dedup UNIQUE (
                operation_hash, launch_id, user_id, sale_option_id,
                batch_index, source, timestamp
            );

        PERFORM create_hypertable('launchpad_purchase_event', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    END IF;
END $$;
