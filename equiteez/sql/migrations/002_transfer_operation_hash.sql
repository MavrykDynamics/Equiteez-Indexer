-- operation_hash: Mavryk operation hash for transfer traceability

ALTER TABLE user_token_transfer
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_user_token_transfer_operation_hash
    ON user_token_transfer (operation_hash);
