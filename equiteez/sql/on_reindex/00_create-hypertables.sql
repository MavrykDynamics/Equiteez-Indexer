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
