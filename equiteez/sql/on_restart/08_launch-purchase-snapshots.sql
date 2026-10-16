-- Nullable purchase-time facts. No historical inference/backfill.
ALTER TABLE launchpad_purchase_event
    ADD COLUMN IF NOT EXISTS price NUMERIC NULL,
    ADD COLUMN IF NOT EXISTS total NUMERIC NULL,
    ADD COLUMN IF NOT EXISTS token_distribution_type SMALLINT NULL,
    ADD COLUMN IF NOT EXISTS operation_counter BIGINT NOT NULL DEFAULT -1,
    ADD COLUMN IF NOT EXISTS operation_nonce INT NOT NULL DEFAULT -1;

DO $$
DECLARE
    constraint_name text;
BEGIN
    -- Replace only the old purchase dedup key; preserve primary keys and IDs.
    FOR constraint_name IN
        SELECT c.conname FROM pg_constraint c
        WHERE c.conrelid = 'launchpad_purchase_event'::regclass AND c.contype = 'u'
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a
                 ON a.attrelid = c.conrelid AND a.attnum = k)
            IN (ARRAY['batch_index','launch_id','operation_hash','sale_option_id','source','timestamp','user_id'], ARRAY['batch_index','launch_id','operation_hash','sale_option_id','source','user_id'])
    LOOP
        EXECUTE format('ALTER TABLE launchpad_purchase_event DROP CONSTRAINT %I', constraint_name);
    END LOOP;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'launchpad_purchase_event'::regclass AND conname = 'launchpad_purchase_snapshot_naturals') THEN
        ALTER TABLE launchpad_purchase_event ADD CONSTRAINT launchpad_purchase_snapshot_naturals CHECK (
            (price IS NULL OR (price >= 0 AND price < 'Infinity'::numeric AND price = trunc(price))) AND
            (total IS NULL OR (total >= 0 AND total < 'Infinity'::numeric AND total = trunc(total)))
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_index i
        WHERE i.indrelid = 'launchpad_purchase_event'::regclass AND i.indisunique
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(i.indkey) k JOIN pg_attribute a
                 ON a.attrelid = i.indrelid AND a.attnum = k)
            = ARRAY['batch_index','launch_id','operation_counter','operation_hash','operation_nonce','sale_option_id','source','timestamp','user_id']
    ) THEN
        CREATE UNIQUE INDEX launchpad_purchase_event_call_dedup
            ON launchpad_purchase_event (operation_hash, launch_id, user_id, sale_option_id,
                batch_index, source, timestamp, operation_counter, operation_nonce);
    END IF;
END $$;
