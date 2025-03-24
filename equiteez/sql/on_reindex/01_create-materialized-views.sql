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
