-- Heal what `dipdup schema wipe` leaves behind: a table whose drop is blocked by
-- a continuous aggregate with a dependent view survives it, but CASCADE still
-- takes its FK constraints and its id sequence, and CREATE TABLE IF NOT EXISTS
-- then skips the survivor — leaving Hasura unable to build relationships and the
-- first insert dying on a null id. Drop-then-add because Postgres has no ADD
-- CONSTRAINT IF NOT EXISTS; free here, 00_create-hypertables.sql has already
-- emptied these tables. No-op on a clean database.
DO $$
DECLARE
    fk record;
    seq_tbl text;
BEGIN
    FOR fk IN
        SELECT * FROM (VALUES
            ('dodo_mav',                     'dodo_mav_base_token_id_fkey',                    'base_token_id',     'token'),
            ('dodo_mav',                     'dodo_mav_quote_token_id_fkey',                   'quote_token_id',    'token'),
            ('dodo_mav',                     'dodo_mav_base_lp_token_id_fkey',                 'base_lp_token_id',  'token'),
            ('dodo_mav',                     'dodo_mav_quote_lp_token_id_fkey',                'quote_lp_token_id', 'token'),
            ('dodo_mav',                     'dodo_mav_rwa_orderbook_id_fkey',                 'rwa_orderbook_id',  'orderbook'),
            ('dodo_mav_history_data',        'dodo_mav_history_data_trader_id_fkey',           'trader_id',         'equiteez_user'),
            ('dodo_mav_history_data',        'dodo_mav_history_data_dodo_mav_id_fkey',         'dodo_mav_id',       'dodo_mav'),
            ('launchpad_purchase_event',     'launchpad_purchase_event_launch_id_fkey',        'launch_id',         'launchpad_launch'),
            ('launchpad_purchase_event',     'launchpad_purchase_event_user_id_fkey',          'user_id',           'equiteez_user'),
            ('launchpad_purchase_event',     'launchpad_purchase_event_sale_option_id_fkey',   'sale_option_id',    'launchpad_sale_option'),
            ('launchpad_purchase_event',     'launchpad_purchase_event_payment_token_id_fkey', 'payment_token_id',  'token'),
            ('orderbook_order_event',        'orderbook_order_event_orderbook_id_fkey',        'orderbook_id',      'orderbook'),
            ('orderbook_order_event',        'orderbook_order_event_order_id_fkey',            'order_id',          'orderbook_order'),
            ('orderbook_order_event',        'orderbook_order_event_initiator_id_fkey',        'initiator_id',      'equiteez_user'),
            ('orderbook_order_event',        'orderbook_order_event_currency_id_fkey',         'currency_id',       'orderbook_currency'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_token_id_fkey',     'token_id',          'token'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_from_user_id_fkey', 'from_user_id',      'equiteez_user'),
            ('equiteez_user_token_transfer', 'equiteez_user_token_transfer_to_user_id_fkey',   'to_user_id',        'equiteez_user')
        ) AS t(tbl, conname, col, reftbl)
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I', fk.tbl, fk.conname);
        EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(id) ON DELETE CASCADE',
            fk.tbl, fk.conname, fk.col, fk.reftbl
        );
    END LOOP;

    FOREACH seq_tbl IN ARRAY ARRAY[
        'dodo_mav',
        'dodo_mav_history_data',
        'launchpad_purchase_event',
        'orderbook_order_event'
    ]
    LOOP
        EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %I OWNED BY %I.id', seq_tbl || '_id_seq', seq_tbl);
        EXECUTE format('ALTER TABLE %I ALTER COLUMN id SET DEFAULT nextval(%L)', seq_tbl, seq_tbl || '_id_seq');
    END LOOP;
END $$;
