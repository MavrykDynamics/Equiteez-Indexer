-- 24h RWA trading volume per token, denominated in RWA token units.

CREATE MATERIALIZED VIEW IF NOT EXISTS rwa_volume_24h_tokens AS
SELECT
    o.rwa_token_id           AS token_id,
    SUM(oo.fulfilled_amount) AS volume_24h_tokens,
    now()                    AS computed_at
FROM orderbook o
JOIN orderbook_order oo ON oo.orderbook_id = o.id
WHERE oo.order_type = 1                                  -- OrderType.SELL (BUY=0, SELL=1)
  AND oo.created_at >= now() - INTERVAL '24 hours'
GROUP BY o.rwa_token_id;

CREATE UNIQUE INDEX IF NOT EXISTS uq_rwa_volume_24h_tokens_token_id
    ON rwa_volume_24h_tokens(token_id);
