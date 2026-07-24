-- Live order-book depth: one row per (orderbook, side, raw price tick) with the
-- summed unfulfilled remainder and the number of orders behind the tick.
--
-- Consumed by mavryk-rwa-backend's GET /assets/{addr}/orderbook through Hasura
-- as a plain table (order_by price + limit + offset), so pagination happens
-- AFTER aggregation — requesting 20 rows returns 20 price levels, not 20 raw
-- orders. A plain (non-materialized) VIEW on purpose: depth is trading data the
-- backend never serves stale, and per-book aggregation is cheap via the partial
-- index below.
--
-- The open-order predicate mirrors the backend's buySellRWAOrders query
-- (is_* flags all false, unfulfilled remainder > 0), plus one deliberate
-- improvement: orders past their expiry that no on-chain clear_expired_orders
-- has flagged yet (is_expired only flips on an on-chain event) are excluded —
-- they are not matchable and would otherwise show up as phantom depth.
CREATE OR REPLACE VIEW orderbook_depth_level_view AS
SELECT
    o.id                       AS orderbook_id,
    o.address                  AS orderbook_address,
    o.in_allowlist             AS in_allowlist,
    oo.order_type              AS order_type,          -- 0 = buy, 1 = sell
    oo.price_per_rwa_token     AS price,               -- raw tick (bigint)
    SUM(oo.unfulfilled_amount) AS amount,              -- raw remainder (numeric)
    COUNT(*)                   AS orders_count
FROM orderbook_order oo
JOIN orderbook o ON o.id = oo.orderbook_id
WHERE oo.unfulfilled_amount > 0
  AND oo.is_fulfilled = false
  AND oo.is_canceled  = false
  AND oo.is_expired   = false
  AND oo.is_refunded  = false
  AND (oo.order_expiry IS NULL OR oo.order_expiry > now())
GROUP BY o.id, o.address, o.in_allowlist, oo.order_type, oo.price_per_rwa_token;

-- Partial covering index matching the view's open-order predicate (minus the
-- volatile now() expiry check, which is evaluated per query on the small open
-- remainder). Lets the planner GroupAggregate in index order and stop at the
-- LIMIT, so a top-N depth page costs ~(orders in the top N levels) regardless
-- of the book's total size; bids read the same index backward.
CREATE INDEX IF NOT EXISTS idx_orderbook_order_open_depth
    ON orderbook_order (orderbook_id, order_type, price_per_rwa_token)
    INCLUDE (unfulfilled_amount)
    WHERE is_fulfilled = false AND is_canceled = false
      AND is_expired  = false AND is_refunded = false
      AND unfulfilled_amount > 0;
