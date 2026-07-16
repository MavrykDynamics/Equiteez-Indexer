-- Heal the aftermath of `dipdup schema wipe` on TimescaleDB.
--
-- dipdup_wipe() drops every table with CASCADE and silently swallows
-- errors. Tables whose dependency chain contains a continuous aggregate
-- with a dependent plain view (dodo_mav_history_data, launchpad_purchase_event
-- via the candle/rollup *_view wrappers, and dodo_mav via the candles'
-- direct views) FAIL to drop and survive the wipe — keeping their rows
-- but losing the FK constraints that pointed at the dropped tables
-- (cascade eats them). The next safe CREATE TABLE IF NOT EXISTS skips
-- the survivors, so without this file the rows stay stale and Hasura's
-- `replace_metadata` fails with 400 (relationships require real
-- constraints). Idempotent: no-op on a genuinely clean database.
-- (Stale ROWS of the survivors are cleared earlier, at the top of
-- 00_create-hypertables.sql, before hypertable/cagg creation.)
DO $$
DECLARE
    fk record;
BEGIN
    FOR fk IN
        SELECT * FROM (VALUES
            ('dodo_mav_history_data',    'dodo_mav_history_data_trader_id_fkey',           'trader_id',        'equiteez_user'),
            ('dodo_mav_history_data',    'dodo_mav_history_data_dodo_mav_id_fkey',         'dodo_mav_id',      'dodo_mav'),
            ('launchpad_purchase_event', 'launchpad_purchase_event_launch_id_fkey',        'launch_id',        'launchpad_launch'),
            ('launchpad_purchase_event', 'launchpad_purchase_event_user_id_fkey',          'user_id',          'equiteez_user'),
            ('launchpad_purchase_event', 'launchpad_purchase_event_sale_option_id_fkey',   'sale_option_id',   'launchpad_sale_option'),
            ('launchpad_purchase_event', 'launchpad_purchase_event_payment_token_id_fkey', 'payment_token_id', 'token'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_token_id_fkey',     'token_id',     'token'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_from_user_id_fkey', 'from_user_id', 'equiteez_user'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_to_user_id_fkey',   'to_user_id',   'equiteez_user'),
            ('dodo_mav', 'dodo_mav_base_token_id_fkey',     'base_token_id',     'token'),
            ('dodo_mav', 'dodo_mav_quote_token_id_fkey',    'quote_token_id',    'token'),
            ('dodo_mav', 'dodo_mav_base_lp_token_id_fkey',  'base_lp_token_id',  'token'),
            ('dodo_mav', 'dodo_mav_quote_lp_token_id_fkey', 'quote_lp_token_id', 'token'),
            ('dodo_mav', 'dodo_mav_rwa_orderbook_id_fkey',  'rwa_orderbook_id',  'orderbook')
        ) AS t(tbl, conname, col, reftbl)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = fk.conname) THEN
            EXECUTE format(
                'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(id) ON DELETE CASCADE',
                fk.tbl, fk.conname, fk.col, fk.reftbl
            );
        END IF;
    END LOOP;
END $$;
