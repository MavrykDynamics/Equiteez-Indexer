-- operation_hash: Mavryk operation hash on orderbook orders
ALTER TABLE orderbook_order
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_orderbook_order_operation_hash
    ON orderbook_order (operation_hash);

-- unique_together from Meta never reaches an existing table (it sits inside
-- CREATE TABLE IF NOT EXISTS); the guard matches either form by definition.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'orderbook_order'
          AND indexdef ILIKE 'CREATE UNIQUE INDEX%(orderbook_id, order_type, order_id)%'
    ) THEN
        -- Duplicates from the old blind-INSERT placement handlers; keep the earliest
        DELETE FROM orderbook_order a
            USING orderbook_order b
            WHERE a.orderbook_id = b.orderbook_id
              AND a.order_type   = b.order_type
              AND a.order_id     = b.order_id
              AND a.id > b.id;

        CREATE UNIQUE INDEX uq_orderbook_order_identity
            ON orderbook_order (orderbook_id, order_type, order_id);
    END IF;
END $$;

-- Removed from Meta (a prefix of the unique index above); Tortoise never drops
-- indexes on an existing table, so do it here.
DO $$
DECLARE
    stale text;
BEGIN
    SELECT indexname INTO stale FROM pg_indexes
    WHERE tablename = 'orderbook_order'
      AND indexdef ILIKE 'CREATE INDEX%(orderbook_id, order_type)';
    IF stale IS NOT NULL THEN
        EXECUTE format('DROP INDEX %I', stale);
    END IF;
END $$;

-- orderbook_order_event first shipped without currency_id and with batch_index 0
-- for a top-level transaction; the next revision added the column and moved
-- top-level to -1. Tortoise's safe DDL never alters an existing table, so a
-- database that ran the first revision keeps the old shape, and as a hypertable
-- the table even survives `dipdup schema wipe`. A fresh database gets the new
-- shape from CREATE TABLE and both blocks below are no-ops.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orderbook_order_event'
          AND column_name = 'currency_id'
          AND is_nullable = 'NO'
    ) THEN
        -- Unnamed REFERENCES gets the Postgres default name, the same one Tortoise
        -- produces on a fresh database and 08_restore-foreign-keys.sql expects
        ALTER TABLE orderbook_order_event
            ADD COLUMN IF NOT EXISTS currency_id INT
                REFERENCES orderbook_currency (id) ON DELETE CASCADE;

        UPDATE orderbook_order_event e
            SET currency_id = o.currency_id
            FROM orderbook_order o
            WHERE o.id = e.order_id
              AND e.currency_id IS NULL;

        ALTER TABLE orderbook_order_event
            ALTER COLUMN currency_id SET NOT NULL;
    END IF;
END $$;

-- Old rows carry batch_index 0 for top-level transactions and would miss the
-- dedup key on a replay, so the replayed range would be written twice. Every
-- orderbook transaction seen so far is top-level (600 sampled), so rewriting all
-- zeros is exact; the old DEFAULT 0 marks a table the rewrite has not reached.
DO $$
BEGIN
    IF (
        SELECT column_default FROM information_schema.columns
        WHERE table_name = 'orderbook_order_event'
          AND column_name = 'batch_index'
    ) = '0' THEN
        UPDATE orderbook_order_event SET batch_index = -1 WHERE batch_index = 0;
        ALTER TABLE orderbook_order_event ALTER COLUMN batch_index SET DEFAULT -1;
    END IF;
END $$;

-- operation_hash: Mavryk operation hash on user-token transfers
ALTER TABLE equiteez_user_token_transfer
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_equiteez_user_token_transfer_operation_hash
    ON equiteez_user_token_transfer (operation_hash);

-- operation_hash: Mavryk operation hash that initiated a super-admin signatory action
ALTER TABLE super_admin_signatory_action
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_super_admin_signatory_action_operation_hash
    ON super_admin_signatory_action (operation_hash);

-- DualCursor: updated_at on domain tables; last_updated_at on *lambda tables.
-- Indexes (cursor column ASC, id ASC) for polling.
ALTER TABLE token          ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE equiteez_user  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE orderbook                       ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_lambda                ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_entrypoint_status     ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_currency              ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_rwa_order             ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_rwa_order_buy_price   ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_rwa_order_sell_price  ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_rwa_order_buy_order   ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_rwa_order_sell_order  ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE orderbook_order                 ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE kyc                          ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_lambda                   ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_entrypoint_status        ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_valid_input              ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_registrar                ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_country_transfer_rule    ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE kyc_member                   ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE super_admin                          ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_lambda                   ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_signatory                ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_user_role                ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_signatory_action         ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_signatory_action_data    ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_token_updated_at_id          ON token          (updated_at ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_equiteez_user_updated_at_id  ON equiteez_user  (updated_at ASC, id ASC);

CREATE INDEX IF NOT EXISTS idx_orderbook_updated_at_id                       ON orderbook                       (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_lambda_last_updated_at_id           ON orderbook_lambda                (last_updated_at ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_entrypoint_status_updated_at_id     ON orderbook_entrypoint_status     (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_currency_updated_at_id              ON orderbook_currency              (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_rwa_order_updated_at_id             ON orderbook_rwa_order             (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_rwa_order_buy_price_updated_at_id   ON orderbook_rwa_order_buy_price   (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_rwa_order_sell_price_updated_at_id  ON orderbook_rwa_order_sell_price  (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_rwa_order_buy_order_updated_at_id   ON orderbook_rwa_order_buy_order   (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_rwa_order_sell_order_updated_at_id  ON orderbook_rwa_order_sell_order  (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_orderbook_order_updated_at_id                 ON orderbook_order                 (updated_at      ASC, id ASC);

CREATE INDEX IF NOT EXISTS idx_kyc_updated_at_id                       ON kyc                       (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_lambda_last_updated_at_id           ON kyc_lambda                (last_updated_at ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_entrypoint_status_updated_at_id     ON kyc_entrypoint_status     (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_valid_input_updated_at_id           ON kyc_valid_input           (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_registrar_updated_at_id             ON kyc_registrar             (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_country_transfer_rule_updated_at_id ON kyc_country_transfer_rule (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_kyc_member_updated_at_id                ON kyc_member                (updated_at      ASC, id ASC);

CREATE INDEX IF NOT EXISTS idx_super_admin_updated_at_id                       ON super_admin                       (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_lambda_last_updated_at_id           ON super_admin_lambda                (last_updated_at ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_signatory_updated_at_id             ON super_admin_signatory             (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_user_role_updated_at_id             ON super_admin_user_role             (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_signatory_action_updated_at_id      ON super_admin_signatory_action      (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_signatory_action_data_updated_at_id ON super_admin_signatory_action_data (updated_at      ASC, id ASC);

-- in_allowlist on domain contract tables (Token, Orderbook, Kyc, SuperAdmin)
ALTER TABLE token       ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orderbook   ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE kyc         ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE super_admin ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_token_in_allowlist       ON token       (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_orderbook_in_allowlist   ON orderbook   (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_kyc_in_allowlist         ON kyc         (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_super_admin_in_allowlist ON super_admin (in_allowlist);
