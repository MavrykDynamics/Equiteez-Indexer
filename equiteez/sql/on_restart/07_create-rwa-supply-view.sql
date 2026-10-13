-- This feature merges the old token and launchpad indexes. Never bootstrap
-- balances from an already-advanced stream: deploy to a fully reindexed DB.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM dipdup_index
               WHERE name IN ('token_index', 'launchpad_index') AND level > 0) THEN
        RAISE EXCEPTION 'RWA supply requires a full DipDup schema reindex before startup';
    END IF;
END $$;

-- DISTINCT prevents double subtraction when campaigns share a treasury.
-- A token without a launch has no exclusions. Orderbook escrow stays circulating.
CREATE OR REPLACE VIEW rwa_supply_view AS
WITH excluded AS (
    SELECT DISTINCT t.address AS contract, t.token_id::text AS token_id,
                    tr.treasury_address
    FROM token_launch_treasury tr JOIN token t ON t.id = tr.token_id
), amounts AS (
    SELECT s.id, s.contract, s.token_id, s.total_supply_raw,
           COALESCE(SUM(b.balance_raw), 0) AS ledger_supply_raw,
           COALESCE(SUM(CASE WHEN e.treasury_address IS NOT NULL
                            THEN b.balance_raw ELSE 0 END), 0) AS excluded_supply_raw
    FROM rwa_token_supply s
    LEFT JOIN rwa_token_balance b ON b.token_id = s.id
    LEFT JOIN excluded e ON e.contract = s.contract AND e.token_id = s.token_id
                       AND e.treasury_address = b.holder
    GROUP BY s.id, s.contract, s.token_id, s.total_supply_raw
)
SELECT a.id, a.contract, a.token_id, a.total_supply_raw, a.excluded_supply_raw,
       a.total_supply_raw - a.excluded_supply_raw AS circulating_supply_raw,
       i.level AS indexed_level
FROM amounts a
JOIN dipdup_index i ON i.name = 'rwa_index' AND i.status = 'realtime'
-- Incomplete ledger data must never look like a valid supply snapshot.
WHERE a.ledger_supply_raw = a.total_supply_raw;

COMMENT ON VIEW rwa_supply_view IS
'RWA raw supply at the last processed level of rwa_index. Available after synchronization; not a chain-head or finality certificate. No launch means no treasury exclusions.';
