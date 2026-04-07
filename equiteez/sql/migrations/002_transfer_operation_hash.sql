-- operation_hash: Mavryk operation hash for transfer traceability (equiteez_user_token_transfer)

ALTER TABLE equiteez_user_token_transfer
    ADD COLUMN IF NOT EXISTS operation_hash VARCHAR(64) NULL;

CREATE INDEX IF NOT EXISTS idx_equiteez_user_token_transfer_operation_hash
    ON equiteez_user_token_transfer (operation_hash);
