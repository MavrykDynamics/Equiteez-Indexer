-- Per-launch aggregates that are expensive to compute on every request.
-- Refreshed by the `refresh_launchpad_stats` DipDup hook on a schedule.
-- Frontend joins via the launch_id key.

CREATE MATERIALIZED VIEW IF NOT EXISTS launchpad_launch_stats AS
SELECT
    l.id AS launch_id,

    -- Unique buyers in this launch
    (SELECT COUNT(DISTINCT user_id)
     FROM launchpad_purchase
     WHERE launch_id = l.id) AS participant_count,

    -- Number of purchase events
    (SELECT COUNT(*)
     FROM launchpad_purchase_event
     WHERE launch_id = l.id) AS purchase_event_count,

    -- Most recent purchase event timestamp (or sale_start if no purchases yet)
    COALESCE(
        (SELECT MAX(timestamp)
         FROM launchpad_purchase_event
         WHERE launch_id = l.id),
        l.sale_start
    ) AS last_purchase_at,

    -- Total raised per payment token, keyed by token contract address.
    COALESCE(
        (SELECT jsonb_object_agg(payment_token_address, total_paid)
         FROM (
            SELECT
                t.address AS payment_token_address,
                SUM(pe.amount * sop.price)::text AS total_paid
            FROM launchpad_purchase_event pe
            JOIN launchpad_sale_option_payment sop
                ON sop.sale_option_id = pe.sale_option_id
                AND sop.name = pe.payment_name
            LEFT JOIN token t ON sop.token_id = t.id
            WHERE pe.launch_id = l.id
                AND t.address IS NOT NULL
            GROUP BY t.address
         ) per_token),
        '{}'::jsonb
    ) AS total_raised_by_token
FROM launchpad_launch l;

-- Unique index on launch_id is required for REFRESH MATERIALIZED VIEW CONCURRENTLY.
CREATE UNIQUE INDEX IF NOT EXISTS uq_launchpad_launch_stats_launch_id
    ON launchpad_launch_stats(launch_id);
