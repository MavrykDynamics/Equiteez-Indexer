-- Token transfer volume by day
CREATE MATERIALIZED VIEW IF NOT EXISTS token_transfer_volume_daily
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
DO $$ 
BEGIN
    -- Try to drop the policy if it exists
    BEGIN
        PERFORM remove_continuous_aggregate_policy('token_transfer_volume_daily');
    EXCEPTION WHEN undefined_object THEN
        -- Policy doesn't exist, continue
        NULL;
    END;
    
    -- Add new policy
    PERFORM add_continuous_aggregate_policy('token_transfer_volume_daily',
        INTERVAL '30 days',
        INTERVAL '1 hour',
        INTERVAL '1 day');
END $$;
