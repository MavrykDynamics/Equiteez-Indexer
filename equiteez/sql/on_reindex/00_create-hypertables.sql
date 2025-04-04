ALTER TABLE equiteez_user_token_transfer DROP CONSTRAINT equiteez_user_token_transfer_pkey;
ALTER TABLE equiteez_user_token_transfer ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('equiteez_user_token_transfer', 'timestamp', 
                        chunk_time_interval => INTERVAL '1 day',
                        if_not_exists => TRUE);

-- Create hypertable for DodoMavHistoryData
ALTER TABLE dodo_mav_history_data DROP CONSTRAINT dodo_mav_history_data_pkey;
ALTER TABLE dodo_mav_history_data ADD PRIMARY KEY (id, timestamp);
SELECT create_hypertable('dodo_mav_history_data', 'timestamp', 
                        chunk_time_interval => INTERVAL '1 day',
                        if_not_exists => TRUE);
