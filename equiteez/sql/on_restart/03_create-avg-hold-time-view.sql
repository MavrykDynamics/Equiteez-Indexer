-- Average holding time (days) per RWA token, over current holders.

CREATE MATERIALIZED VIEW IF NOT EXISTS token_avg_hold_time AS
WITH treasury AS (
    SELECT DISTINCT l.token_id, tr.address
    FROM launchpad_launch l
    JOIN launchpad_treasury tr ON tr.launchpad_id = l.launchpad_id
    WHERE tr.name = 'launchTreasury' AND l.token_id IS NOT NULL
),
flows AS (
    -- primary purchases (MINT and TRANSFER), inflow
    SELECT l.token_id, pe.user_id AS holder_id, pe.amount::numeric AS amt, pe.timestamp AS ts
    FROM launchpad_purchase_event pe
    JOIN launchpad_launch l ON l.id = pe.launch_id
    WHERE l.token_id IS NOT NULL
    UNION ALL
    -- orderbook BUY fills, inflow to the buyer (initiator)
    SELECT o.rwa_token_id, oo.initiator_id, oo.fulfilled_amount::numeric, COALESCE(oo.ended_at, oo.created_at)
    FROM orderbook_order oo
    JOIN orderbook o ON o.id = oo.orderbook_id
    WHERE oo.order_type = 0 AND oo.fulfilled_amount > 0
    UNION ALL
    -- orderbook SELL fills, outflow from the seller (initiator)
    SELECT o.rwa_token_id, oo.initiator_id, -oo.fulfilled_amount::numeric, COALESCE(oo.ended_at, oo.created_at)
    FROM orderbook_order oo
    JOIN orderbook o ON o.id = oo.orderbook_id
    WHERE oo.order_type = 1 AND oo.fulfilled_amount > 0
    UNION ALL
    -- p2p in / out (tz→tz transfers)
    SELECT tr.token_id, tr.to_user_id, tr.amount::numeric, tr.timestamp
    FROM equiteez_user_token_transfer tr
    UNION ALL
    SELECT tr.token_id, tr.from_user_id, -tr.amount::numeric, tr.timestamp
    FROM equiteez_user_token_transfer tr
),
holder_state AS (
    SELECT token_id, holder_id,
           SUM(amt)                       AS balance,
           MIN(ts) FILTER (WHERE amt > 0) AS first_acquired
    FROM flows
    GROUP BY token_id, holder_id
)
SELECT hs.token_id,
       COUNT(*)                                                       AS holders_count,
       AVG(EXTRACT(EPOCH FROM (now() - hs.first_acquired)) / 86400.0) AS avg_hold_time_days,
       now()                                                          AS computed_at
FROM holder_state hs
JOIN equiteez_user hu ON hu.id = hs.holder_id
WHERE hs.balance > 0
  AND hs.first_acquired IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM treasury t WHERE t.token_id = hs.token_id AND t.address = hu.address)
GROUP BY hs.token_id;

-- Unique index on token_id is required for REFRESH MATERIALIZED VIEW CONCURRENTLY.
CREATE UNIQUE INDEX IF NOT EXISTS uq_token_avg_hold_time_token_id
    ON token_avg_hold_time(token_id);
