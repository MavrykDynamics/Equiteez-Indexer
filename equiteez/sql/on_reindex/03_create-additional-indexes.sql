-- -- Additional indexes specifically for time-series queries
-- CREATE INDEX IF NOT EXISTS idx_token_transfer_token_time 
--     ON equiteez_user_token_transfer(token_id, timestamp DESC);
    
-- CREATE INDEX IF NOT EXISTS idx_token_transfer_from_time 
--     ON equiteez_user_token_transfer(from_user_id, timestamp DESC);
    
-- CREATE INDEX IF NOT EXISTS idx_token_transfer_to_time 
--     ON equiteez_user_token_transfer(to_user_id, timestamp DESC);

-- -- Create indexes for DodoMavHistoryData candles
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1h_dodo_mav_address_bucket ON dodo_mav_candles_1h (dodo_mav_address, bucket DESC);
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1d_dodo_mav_address_bucket ON dodo_mav_candles_1d (dodo_mav_address, bucket DESC);
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1w_dodo_mav_address_bucket ON dodo_mav_candles_1w (dodo_mav_address, bucket DESC);
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1m_dodo_mav_address_bucket ON dodo_mav_candles_1m (dodo_mav_address, bucket DESC);
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_1y_dodo_mav_address_bucket ON dodo_mav_candles_1y (dodo_mav_address, bucket DESC);
-- CREATE INDEX IF NOT EXISTS idx_dodo_mav_candles_3y_dodo_mav_address_bucket ON dodo_mav_candles_3y (dodo_mav_address, bucket DESC);
