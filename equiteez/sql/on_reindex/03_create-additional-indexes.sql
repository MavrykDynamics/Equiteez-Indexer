-- Additional indexes specifically for time-series queries
CREATE INDEX IF NOT EXISTS idx_token_transfer_token_time 
    ON equiteez_user_token_transfer(token_id, timestamp DESC);
    
CREATE INDEX IF NOT EXISTS idx_token_transfer_from_time 
    ON equiteez_user_token_transfer(from_user_id, timestamp DESC);
    
CREATE INDEX IF NOT EXISTS idx_token_transfer_to_time 
    ON equiteez_user_token_transfer(to_user_id, timestamp DESC);

-- Create indexes for DodoMavHistoryData candles
CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1h_dodo_mav_address_bucket ON dodo_mav_candles_1h (dodo_mav_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1d_dodo_mav_address_bucket ON dodo_mav_candles_1d (dodo_mav_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1w_dodo_mav_address_bucket ON dodo_mav_candles_1w (dodo_mav_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1m_dodo_mav_address_bucket ON dodo_mav_candles_1m (dodo_mav_address, timestamp DESC);

-- Launchpad: asset-centric and user-centric query indexes.
CREATE INDEX IF NOT EXISTS idx_launchpad_launch_token
    ON launchpad_launch(token_id);

-- "All my purchases" across launches.
CREATE INDEX IF NOT EXISTS idx_launchpad_purchase_user
    ON launchpad_purchase(user_id);

-- "My event history" across launches, ordered by recency.
CREATE INDEX IF NOT EXISTS idx_launchpad_purchase_event_user_time
    ON launchpad_purchase_event(user_id, timestamp DESC);
