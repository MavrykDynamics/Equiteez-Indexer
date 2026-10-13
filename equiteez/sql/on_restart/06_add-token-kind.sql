-- Existing union allowlist flags do not identify which list matched. Invalidate
-- them once when adding the discriminator; on_restart refreshes both flags from
-- the allowlist. If the fetch fails, unclassified quotes stay out of RWA results.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'token'::regclass
          AND attname = 'is_quote_token'
          AND NOT attisdropped
    ) THEN
        ALTER TABLE token
            ADD COLUMN is_quote_token BOOLEAN NOT NULL DEFAULT FALSE;
        UPDATE token SET in_allowlist = FALSE, updated_at = NOW()
            WHERE in_allowlist;
    END IF;
END $$;

COMMENT ON COLUMN token.is_quote_token IS
    'Whether the token contract is in the quote_tokens allowlist. Filter in_allowlist = true AND is_quote_token = false for RWA assets.';
