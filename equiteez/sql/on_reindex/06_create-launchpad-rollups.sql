-- Continuous aggregates: rollups of launchpad_purchase_event per launch,
-- bucketed by 1h / 1d / 1w. Powers time-series charts on launch pages
-- (purchases velocity, unique buyers over time, volume).

-- 1 hour buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS launchpad_purchase_stats_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    launch_id,
    COUNT(*) AS purchase_count,
    COUNT(DISTINCT user_id) AS unique_buyers,
    SUM(amount) AS total_amount,
    AVG(amount)::bigint AS avg_amount
FROM launchpad_purchase_event
GROUP BY 1, launch_id;

DO $$
BEGIN
    BEGIN
        PERFORM remove_continuous_aggregate_policy('launchpad_purchase_stats_1h');
    EXCEPTION WHEN undefined_object THEN NULL;
    END;
    PERFORM add_continuous_aggregate_policy('launchpad_purchase_stats_1h',
        INTERVAL '1 day',
        INTERVAL '1 hour',
        INTERVAL '1 hour');
END $$;

CALL refresh_continuous_aggregate('launchpad_purchase_stats_1h', NULL, NULL);

-- 1 day buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS launchpad_purchase_stats_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    launch_id,
    COUNT(*) AS purchase_count,
    COUNT(DISTINCT user_id) AS unique_buyers,
    SUM(amount) AS total_amount,
    AVG(amount)::bigint AS avg_amount
FROM launchpad_purchase_event
GROUP BY 1, launch_id;

DO $$
BEGIN
    BEGIN
        PERFORM remove_continuous_aggregate_policy('launchpad_purchase_stats_1d');
    EXCEPTION WHEN undefined_object THEN NULL;
    END;
    PERFORM add_continuous_aggregate_policy('launchpad_purchase_stats_1d',
        INTERVAL '7 days',
        INTERVAL '1 day',
        INTERVAL '1 day');
END $$;

CALL refresh_continuous_aggregate('launchpad_purchase_stats_1d', NULL, NULL);

-- 1 week buckets
CREATE MATERIALIZED VIEW IF NOT EXISTS launchpad_purchase_stats_1w
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', timestamp) AS bucket,
    launch_id,
    COUNT(*) AS purchase_count,
    COUNT(DISTINCT user_id) AS unique_buyers,
    SUM(amount) AS total_amount,
    AVG(amount)::bigint AS avg_amount
FROM launchpad_purchase_event
GROUP BY 1, launch_id;

DO $$
BEGIN
    BEGIN
        PERFORM remove_continuous_aggregate_policy('launchpad_purchase_stats_1w');
    EXCEPTION WHEN undefined_object THEN NULL;
    END;
    PERFORM add_continuous_aggregate_policy('launchpad_purchase_stats_1w',
        INTERVAL '1 month',
        INTERVAL '1 week',
        INTERVAL '1 week');
END $$;

CALL refresh_continuous_aggregate('launchpad_purchase_stats_1w', NULL, NULL);
