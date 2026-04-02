-- operation_hash: Mavryk operation hash

ALTER TABLE orderbook_order
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_orderbook_order_operation_hash
    ON orderbook_order (operation_hash);
