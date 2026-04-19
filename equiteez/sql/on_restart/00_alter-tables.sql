-- operation_hash: Mavryk operation hash on orderbook orders
ALTER TABLE orderbook_order
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_orderbook_order_operation_hash
    ON orderbook_order (operation_hash);

-- operation_hash: Mavryk operation hash on user-token transfers
ALTER TABLE equiteez_user_token_transfer
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_equiteez_user_token_transfer_operation_hash
    ON equiteez_user_token_transfer (operation_hash);

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
ALTER TABLE super_admin_general_admin            ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE super_admin_contract_admin           ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW();
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
CREATE INDEX IF NOT EXISTS idx_super_admin_general_admin_updated_at_id         ON super_admin_general_admin         (updated_at      ASC, id ASC);
CREATE INDEX IF NOT EXISTS idx_super_admin_contract_admin_updated_at_id        ON super_admin_contract_admin        (updated_at      ASC, id ASC);
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
