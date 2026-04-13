-- in_allowlist on domain contract tables (Token, Orderbook, Kyc, SuperAdmin).

ALTER TABLE token       ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE orderbook   ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE kyc         ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE super_admin ADD COLUMN IF NOT EXISTS in_allowlist BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_token_in_allowlist       ON token (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_orderbook_in_allowlist   ON orderbook (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_kyc_in_allowlist         ON kyc (in_allowlist);
CREATE INDEX IF NOT EXISTS idx_super_admin_in_allowlist ON super_admin (in_allowlist);
