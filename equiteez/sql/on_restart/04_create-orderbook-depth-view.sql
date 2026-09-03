-- Live order-book depth: one row per (orderbook, side, raw price tick) with the
-- summed unfulfilled remainder and the number of orders behind the tick.
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
  AND oo.is_market_order = false
  AND (oo.order_expiry IS NULL OR oo.order_expiry > now())
GROUP BY o.id, o.address, o.in_allowlist, oo.order_type, oo.price_per_rwa_token;

-- CREATE INDEX IF NOT EXISTS never rebuilds an existing index: drop the version
-- predating the is_market_order predicate first.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'orderbook_order'
          AND indexname = 'idx_orderbook_order_open_depth'
          AND indexdef NOT LIKE '%is_market_order%'
    ) THEN
        DROP INDEX idx_orderbook_order_open_depth;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_orderbook_order_open_depth
    ON orderbook_order (orderbook_id, order_type, price_per_rwa_token)
    INCLUDE (unfulfilled_amount)
    WHERE is_fulfilled = false AND is_canceled = false
      AND is_expired  = false AND is_refunded = false
      AND is_market_order = false
      AND unfulfilled_amount > 0;
