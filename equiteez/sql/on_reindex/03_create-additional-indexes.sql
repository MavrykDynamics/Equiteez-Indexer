-- Additional indexes specifically for time-series queries
CREATE INDEX IF NOT EXISTS idx_token_transfer_token_time 
    ON equiteez_user_token_transfer(token_id, timestamp DESC);
    
CREATE INDEX IF NOT EXISTS idx_token_transfer_from_time 
    ON equiteez_user_token_transfer(from_user_id, timestamp DESC);
    
CREATE INDEX IF NOT EXISTS idx_token_transfer_to_time 
    ON equiteez_user_token_transfer(to_user_id, timestamp DESC);
