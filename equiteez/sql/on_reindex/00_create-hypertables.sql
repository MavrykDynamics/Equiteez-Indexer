-- -- Create hypertable for equiteez_user_token_transfer
-- DO $$ 
-- BEGIN
--     IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'equiteez_user_token_transfer_pkey') THEN
--         ALTER TABLE equiteez_user_token_transfer DROP CONSTRAINT equiteez_user_token_transfer_pkey;
--     END IF;
--     ALTER TABLE equiteez_user_token_transfer ADD PRIMARY KEY (id, timestamp);
-- END $$;

-- SELECT create_hypertable('equiteez_user_token_transfer', 'timestamp', 
--                         chunk_time_interval => INTERVAL '1 day',
--                         if_not_exists => TRUE);

-- -- Check if DodoMavHistoryData is already a hypertable
-- DO $$ 
-- DECLARE
--     is_hypertable boolean;
-- BEGIN
--     -- Check if table is already a hypertable
--     SELECT EXISTS (
--         SELECT 1 
--         FROM timescaledb_information.hypertables 
--         WHERE hypertable_name = 'dodo_mav_history_data'
--     ) INTO is_hypertable;

--     -- Only proceed if not already a hypertable
--     IF NOT is_hypertable THEN
--         -- Drop existing primary key if it exists
--         IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dodo_mav_history_data_pkey') THEN
--             ALTER TABLE dodo_mav_history_data DROP CONSTRAINT dodo_mav_history_data_pkey;
--         END IF;
        
--         -- Add new primary key
--         ALTER TABLE dodo_mav_history_data ADD PRIMARY KEY (id, timestamp);
        
--         -- Create hypertable
--         PERFORM create_hypertable('dodo_mav_history_data', 'timestamp', 
--                                 chunk_time_interval => INTERVAL '1 day',
--                                 if_not_exists => TRUE,
--                                 migrate_data => TRUE);
--     END IF;
-- END $$;

-- -- Note: Compression settings will be added later if needed
-- -- We can add them in a separate migration after confirming the hypertable works correctly
