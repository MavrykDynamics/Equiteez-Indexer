-- Token transfer volume by day
CREATE MATERIALIZED VIEW token_transfer_volume_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS day,
    token_id,
    transfer_type,
    SUM(amount) AS total_volume,
    COUNT(*) AS transfer_count
FROM equiteez_user_token_transfer
GROUP BY 1, 2, 3
WITH NO DATA;

-- Select an appropriate refresh policy
SELECT add_continuous_aggregate_policy('token_transfer_volume_daily',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 day');

-- Create materialized views for DodoMavHistoryData candles with optimized settings
CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;

-- Drop existing policy if it exists and add new one for 1h candles
DO $$ 
BEGIN
    -- Try to drop the policy if it exists
    BEGIN
        PERFORM remove_continuous_aggregate_policy('dodo_mav_candles_1h');
    EXCEPTION WHEN undefined_object THEN
        -- Policy doesn't exist, continue
        NULL;
    END;
    
    -- Add new policy
    PERFORM add_continuous_aggregate_policy('dodo_mav_candles_1h',
        start_offset => INTERVAL '1 day',
        end_offset => INTERVAL '1 hour',
        schedule_interval => INTERVAL '2 hours');
END $$;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;

-- Drop existing policy if it exists and add new one for 1d candles
DO $$ 
BEGIN
    -- Try to drop the policy if it exists
    BEGIN
        PERFORM remove_continuous_aggregate_policy('dodo_mav_candles_1d');
    EXCEPTION WHEN undefined_object THEN
        -- Policy doesn't exist, continue
        NULL;
    END;
    
    -- Add new policy
    PERFORM add_continuous_aggregate_policy('dodo_mav_candles_1d',
        start_offset => INTERVAL '7 days',
        end_offset => INTERVAL '1 day',
        schedule_interval => INTERVAL '2 days');
END $$;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1w
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;

-- Drop existing policy if it exists and add new one for 1w candles
DO $$ 
BEGIN
    -- Try to drop the policy if it exists
    BEGIN
        PERFORM remove_continuous_aggregate_policy('dodo_mav_candles_1w');
    EXCEPTION WHEN undefined_object THEN
        -- Policy doesn't exist, continue
        NULL;
    END;
    
    -- Add new policy
    PERFORM add_continuous_aggregate_policy('dodo_mav_candles_1w',
        start_offset => INTERVAL '1 month',
        end_offset => INTERVAL '1 week',
        schedule_interval => INTERVAL '2 weeks');
END $$;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;

-- Drop existing policy if it exists and add new one for 1m candles
DO $$ 
BEGIN
    -- Try to drop the policy if it exists
    BEGIN
        PERFORM remove_continuous_aggregate_policy('dodo_mav_candles_1m');
    EXCEPTION WHEN undefined_object THEN
        -- Policy doesn't exist, continue
        NULL;
    END;
    
    -- Add new policy
    PERFORM add_continuous_aggregate_policy('dodo_mav_candles_1m',
        start_offset => INTERVAL '3 months',
        end_offset => INTERVAL '1 month',
        schedule_interval => INTERVAL '2 months');
END $$;

-- For yearly and 3-yearly views, use regular views instead of materialized views
-- to reduce memory usage and background worker load
CREATE OR REPLACE VIEW dodo_mav_candles_1y_view AS
SELECT
    time_bucket('1 year', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;

CREATE OR REPLACE VIEW dodo_mav_candles_3y_view AS
SELECT
    time_bucket('3 years', h.timestamp) AS timestamp,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY 1, m.address;
