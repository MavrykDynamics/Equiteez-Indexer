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

-- Create materialized views for DodoMavHistoryData candles
CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1w
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_1y
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 year', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;

CREATE MATERIALIZED VIEW IF NOT EXISTS dodo_mav_candles_3y
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('3 years', h.timestamp) AS bucket,
    m.address as dodo_mav_address,
    FIRST(h.base_token_price, h.timestamp) as open,
    MAX(h.base_token_price) as high,
    MIN(h.base_token_price) as low,
    LAST(h.base_token_price, h.timestamp) as close,
    SUM(h.base_token_qty) as volume,
    COUNT(*) as trades
FROM dodo_mav_history_data h
JOIN dodo_mav m ON h.dodo_mav_id = m.id
GROUP BY bucket, m.address;
