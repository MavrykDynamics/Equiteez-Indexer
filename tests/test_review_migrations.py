"""Exercise review migrations against a disposable TimescaleDB instance.

Run: RUN_MIGRATION_TESTS=1 python tests/test_review_migrations.py
Requires Docker and the local timescale/timescaledb:2.26.4-pg16 image. The test
container has no network, published ports, or host mounts, and is removed on exit.
Fixtures model the old and current table shapes using only migration dependencies.
"""

import asyncio
import os
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path


SQL_ROOT = Path(__file__).resolve().parents[1] / "equiteez" / "sql"
IMAGE = "timescale/timescaledb:2.26.4-pg16"


@unittest.skipUnless(
    os.environ.get("RUN_MIGRATION_TESTS") == "1",
    "Set RUN_MIGRATION_TESTS=1 to run isolated Docker integration tests",
)
class ReviewMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = f"equiteez-migration-test-{uuid.uuid4().hex[:12]}"
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-d",
                "--name",
                cls.container,
                "--network",
                "none",
                "--pull",
                "never",
                "-e",
                "POSTGRES_HOST_AUTH_METHOD=trust",
                IMAGE,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.addClassCleanup(cls.remove_container)
        for _ in range(60):
            ready = subprocess.run(
                [
                    "docker",
                    "exec",
                    cls.container,
                    "pg_isready",
                    "-h",
                    "127.0.0.1",
                    "-U",
                    "postgres",
                ],
                capture_output=True,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Temporary PostgreSQL instance did not become ready")
        cls.sql("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    @classmethod
    def remove_container(cls):
        subprocess.run(
            ["docker", "rm", "-f", cls.container],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def sql(cls, sql):
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                cls.container,
                "psql",
                "-X",
                "-qAt",
                "-v",
                "ON_ERROR_STOP=1",
                "-h",
                "127.0.0.1",
                "-U",
                "postgres",
                "-d",
                "postgres",
            ],
            input=sql,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def setUp(self):
        self.schema = f"active_{uuid.uuid4().hex[:8]}"
        self.decoy = f"decoy_{uuid.uuid4().hex[:8]}"
        self.sql(f"CREATE SCHEMA {self.schema}; CREATE SCHEMA {self.decoy};")

    def query(self, sql):
        return self.sql(f"SET search_path TO {self.schema}, public;\n{sql}")

    def migrate(self, name):
        self.query((SQL_ROOT / name).read_text())

    def fixtures(self, *, fresh):
        """Minimal dependencies, plus deliberately conflicting objects elsewhere."""
        simple_tables = """
            equiteez_user orderbook_lambda orderbook_entrypoint_status
            orderbook_rwa_order orderbook_rwa_order_buy_price
            orderbook_rwa_order_sell_price orderbook_rwa_order_buy_order
            orderbook_rwa_order_sell_order kyc kyc_lambda kyc_entrypoint_status
            kyc_valid_input kyc_registrar kyc_country_transfer_rule kyc_member
            super_admin super_admin_lambda super_admin_signatory
            super_admin_user_role super_admin_signatory_action
            super_admin_signatory_action_data launchpad launchpad_launch launchpad_sale_option
        """.split()
        self.query(
            "\n".join(
                f"CREATE TABLE {name} (id SERIAL PRIMARY KEY);"
                for name in simple_tables
            )
        )
        # Safe ORM DDL creates the new permit tables before on_restart runs.
        for name in ("kyc_registrar_admin", "kyc_membership_tier", "kyc_membership"):
            self.query(f"""
                CREATE TABLE {name} (
                    id SERIAL PRIMARY KEY, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
        self.query("""
            CREATE TABLE kyc_membership_tier_discount (
                id SERIAL PRIMARY KEY, kyc_id INT, membership_tier TEXT, discount_name TEXT
            );
        """)
        kind = ", is_quote_token BOOLEAN NOT NULL DEFAULT FALSE" if fresh else ""
        currency = (
            ", currency_id INT NOT NULL REFERENCES orderbook_currency(id)"
            if fresh
            else ""
        )
        event_pk = (
            "PRIMARY KEY (id, timestamp)"
            if fresh
            else "CONSTRAINT renamed_event_pk PRIMARY KEY (id)"
        )
        batch_default = -1 if fresh else 0
        self.query(f"""
            CREATE TABLE token (
                id SERIAL PRIMARY KEY, in_allowlist BOOLEAN NOT NULL DEFAULT TRUE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT '2000-01-01'{kind}
            );
            CREATE TABLE orderbook (id SERIAL PRIMARY KEY, address TEXT);
            CREATE TABLE orderbook_currency (id SERIAL PRIMARY KEY);
            CREATE TABLE orderbook_order (
                id SERIAL PRIMARY KEY, orderbook_id INT NOT NULL,
                order_type INT NOT NULL, order_id INT NOT NULL,
                currency_id INT NOT NULL REFERENCES orderbook_currency(id),
                price_per_rwa_token BIGINT DEFAULT 42,
                unfulfilled_amount NUMERIC DEFAULT 5,
                is_fulfilled BOOLEAN DEFAULT FALSE, is_canceled BOOLEAN DEFAULT FALSE,
                is_expired BOOLEAN DEFAULT FALSE, is_refunded BOOLEAN DEFAULT FALSE,
                is_market_order BOOLEAN DEFAULT FALSE, order_expiry TIMESTAMPTZ
            );
            CREATE TABLE orderbook_order_event (
                id SERIAL, timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                order_id INT REFERENCES orderbook_order(id),
                orderbook_id INT, initiator_id INT,
                batch_index INT NOT NULL DEFAULT {batch_default}{currency}, {event_pk}
            );
            CREATE TABLE equiteez_user_token_transfer (
                id SERIAL PRIMARY KEY, token_id INT, from_user_id INT, to_user_id INT
            );
            CREATE TABLE dodo_mav (
                id INT PRIMARY KEY, base_token_id INT, quote_token_id INT,
                base_lp_token_id INT, quote_lp_token_id INT, rwa_orderbook_id INT
            );
            CREATE TABLE dodo_mav_history_data (
                id INT PRIMARY KEY, trader_id INT, dodo_mav_id INT
            );
            CREATE TABLE launchpad_purchase_event (
                id INT PRIMARY KEY, launch_id INT, user_id INT,
                sale_option_id INT, payment_token_id INT
            );
            INSERT INTO token DEFAULT VALUES;
            INSERT INTO orderbook (id, address) VALUES (1, 'KT1orderbook');
            INSERT INTO orderbook_currency (id) VALUES (1);
            INSERT INTO orderbook_order (id, orderbook_id, order_type, order_id, currency_id)
                VALUES (1, 1, 0, 1234, 1);
            CREATE INDEX old_orderbook_prefix ON orderbook_order (orderbook_id, order_type);
        """)
        event_currency = ", currency_id" if fresh else ""
        currency_value = ", 1" if fresh else ""
        self.query(f"""
            INSERT INTO orderbook_order_event
                (id, order_id, orderbook_id, batch_index{event_currency})
                VALUES (1, 1, 1, 0{currency_value});
        """)
        if fresh:
            self.query("""
                CREATE UNIQUE INDEX fresh_order_identity
                    ON orderbook_order (orderbook_id, order_type, order_id);
                SELECT create_hypertable('orderbook_order_event', 'timestamp', migrate_data => TRUE);
            """)
        else:
            self.query("""
                INSERT INTO orderbook_order (id, orderbook_id, order_type, order_id, currency_id)
                    VALUES (2, 1, 0, 1234, 1);
            """)
        self.sql(f"""
            SET search_path TO {self.decoy}, public;
            CREATE TABLE token (id INT PRIMARY KEY, in_allowlist BOOLEAN DEFAULT TRUE,
                                is_quote_token BOOLEAN DEFAULT TRUE);
            INSERT INTO token VALUES (1, TRUE, TRUE);
            CREATE TABLE orderbook_order (id INT PRIMARY KEY, orderbook_id INT,
                                         order_type INT, order_id INT);
            CREATE UNIQUE INDEX uq_orderbook_order_identity
                ON orderbook_order (orderbook_id, order_type, order_id);
            CREATE INDEX old_orderbook_prefix ON orderbook_order (orderbook_id, order_type);
            CREATE INDEX idx_orderbook_order_open_depth ON orderbook_order (orderbook_id);
            CREATE TABLE orderbook_order_event (
                id INT, timestamp TIMESTAMPTZ NOT NULL, batch_index INT DEFAULT 0,
                currency_id INT NOT NULL, PRIMARY KEY (id, timestamp)
            );
            SELECT create_hypertable('orderbook_order_event', 'timestamp');
        """)

    def assert_event_shape(self, expected_batch):
        self.assertEqual(
            self.query("SELECT currency_id, batch_index FROM orderbook_order_event;"),
            f"1|{expected_batch}",
        )
        self.assertEqual(
            self.query("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'orderbook_order_event'
              AND column_name = 'currency_id';
        """),
            "NO",
        )
        self.assertEqual(
            self.query("""
            SELECT COUNT(*) FROM timescaledb_information.hypertables
            WHERE hypertable_schema = current_schema() AND hypertable_name = 'orderbook_order_event';
        """),
            "1",
        )
        comment = self.query("""
            SELECT col_description('orderbook_order_event'::regclass, attnum)
            FROM pg_attribute WHERE attrelid = 'orderbook_order_event'::regclass AND attname = 'order_id';
        """)
        self.assertIn("Internal orderbook_order.id foreign key", comment)
        self.assertIn("orderbook_order.order_id", comment)
        self.assertEqual(
            self.query("""
            SELECT confrelid = 'orderbook_order'::regclass
            FROM pg_constraint WHERE conrelid = 'orderbook_order_event'::regclass
              AND conname = 'orderbook_order_event_order_id_fkey';
        """),
            "t",
        )
        self.assertEqual(self.query("SELECT COUNT(*) FROM orderbook_order;"), "1")
        self.assertEqual(
            self.query("""
            SELECT COUNT(*) FROM pg_indexes WHERE schemaname = current_schema()
              AND indexname = 'old_orderbook_prefix';
        """),
            "0",
        )
        self.assertEqual(
            self.query(f"""
            SELECT COUNT(*) FROM pg_indexes WHERE schemaname = '{self.decoy}'
              AND indexname = 'old_orderbook_prefix';
        """),
            "1",
        )

    def test_old_schema_migrates_despite_same_named_objects_elsewhere(self):
        self.fixtures(fresh=False)
        # on_reindex runs before on_restart, so currency_id is still absent here.
        self.migrate("on_reindex/08_restore-foreign-keys.sql")
        self.migrate("on_reindex/08_restore-foreign-keys.sql")
        self.assertEqual(
            self.query("""
            INSERT INTO dodo_mav DEFAULT VALUES RETURNING id;
        """),
            "1",
        )
        for _ in range(2):
            self.migrate("on_restart/00_alter-tables.sql")
            self.migrate("on_restart/05_convert-order-event-hypertable.sql")
            self.assert_event_shape(expected_batch=-1)
        self.assertEqual(
            self.query("""
            SELECT column_default FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'orderbook_order_event'
              AND column_name = 'batch_index';
        """),
            "'-1'::integer",
        )

    def test_fresh_schema_preserves_real_batch_zero_and_current_depth_index(self):
        self.fixtures(fresh=True)
        self.migrate("on_restart/00_alter-tables.sql")
        self.migrate("on_restart/04_create-orderbook-depth-view.sql")
        index_oid = self.query(
            "SELECT 'idx_orderbook_order_open_depth'::regclass::oid;"
        )
        for _ in range(2):
            self.migrate("on_restart/00_alter-tables.sql")
            self.migrate("on_restart/04_create-orderbook-depth-view.sql")
            self.migrate("on_restart/05_convert-order-event-hypertable.sql")
            self.assert_event_shape(expected_batch=0)
            self.assertEqual(
                self.query("SELECT 'idx_orderbook_order_open_depth'::regclass::oid;"),
                index_oid,
            )
        self.assertEqual(
            self.query("SELECT amount, orders_count FROM orderbook_depth_level_view;"),
            "5|1",
        )
        self.query("UPDATE orderbook_order SET is_market_order = TRUE;")
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM orderbook_depth_level_view;"), "0"
        )

    def test_token_discriminator_invalidates_old_allowlist_once(self):
        self.fixtures(fresh=False)
        self.migrate("on_restart/06_add-token-kind.sql")
        self.assertEqual(
            self.query("""
            SELECT in_allowlist, is_quote_token, updated_at > '2000-01-01'::timestamptz FROM token;
        """),
            "f|f|t",
        )
        self.query("UPDATE token SET in_allowlist = TRUE, is_quote_token = TRUE;")
        self.migrate("on_restart/06_add-token-kind.sql")
        self.assertEqual(
            self.query("SELECT in_allowlist, is_quote_token FROM token;"), "t|t"
        )
        self.assertEqual(
            self.query(f"SELECT in_allowlist, is_quote_token FROM {self.decoy}.token;"),
            "t|t",
        )

    def orm_ddl(self):
        sys.path.insert(0, str(SQL_ROOT.parents[1]))
        from dipdup.database import get_tortoise_config, prepare_models
        from tortoise import Tortoise
        from tortoise.utils import get_schema_sql

        async def generate_sql():
            prepare_models("equiteez")
            await Tortoise.init(
                config=get_tortoise_config(
                    "postgres://postgres@127.0.0.1/postgres", "equiteez"
                )
            )
            try:
                return get_schema_sql(Tortoise.get_connection("default"), safe=True)
            finally:
                await Tortoise.close_connections()

        return asyncio.run(generate_sql())

    def test_orm_startup_tolerates_token_before_discriminator_migration(self):
        # DipDup generates safe ORM DDL before on_restart. A new field description
        # or index would access the missing column before its migration can run.
        ddl = self.orm_ddl()
        self.query(ddl)
        self.query("ALTER TABLE token DROP COLUMN is_quote_token;")
        self.query(ddl)
        self.migrate("on_restart/06_add-token-kind.sql")
        self.assertEqual(
            self.query("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'token'
              AND column_name = 'is_quote_token';
        """),
            "NO",
        )

    def test_kyc_tombstones_upgrade_after_safe_orm_ddl_and_preserve_existing_rows(self):
        ddl = self.orm_ddl()
        self.query(ddl)
        tables = (
            "kyc_registrar_admin",
            "kyc_membership_tier",
            "kyc_membership",
            "kyc_membership_tier_discount",
        )
        self.query("""
            INSERT INTO kyc (id, address) VALUES (1, 'KT1kyc');
            INSERT INTO equiteez_user (id, address) VALUES (1, 'mv1registrar');
            INSERT INTO kyc_registrar (id, kyc_id, user_id) VALUES (1, 1, 1);
            INSERT INTO kyc_registrar_admin (kyc_id, registrar_id, user_id) VALUES (1, 1, 1);
            INSERT INTO kyc_membership_tier (kyc_id, registrar_id, name) VALUES (1, 1, 'Gold');
            INSERT INTO kyc_membership (kyc_id, registrar_id, user_id, tier) VALUES (1, 1, 1, 'Gold');
            INSERT INTO kyc_membership_tier_discount
                (kyc_id, registrar_id, membership_tier, discount_name)
                VALUES (1, 1, 'Gold', 'exitFee');
        """)
        for table in tables:
            self.query(f"""
                UPDATE {table} SET updated_at = '2000-01-01';
                ALTER TABLE {table} DROP COLUMN is_removed;
            """)
        # Existing tables still lack is_removed when DipDup runs its safe DDL.
        # A field description or ORM index on that column would abort startup.
        self.query(ddl)
        for _ in range(2):
            self.migrate("on_restart/00_alter-tables.sql")
            for table in tables:
                self.assertEqual(
                    self.query(f"""
                    SELECT id, is_removed, updated_at = '2000-01-01'::timestamptz
                    FROM {table};
                """),
                    "1|f|t",
                )
                self.assertEqual(
                    self.query(f"""
                    SELECT is_nullable FROM information_schema.columns
                    WHERE table_schema = current_schema() AND table_name = '{table}'
                      AND column_name = 'is_removed';
                """),
                    "NO",
                )
        for table in tables:
            self.query(f"UPDATE {table} SET is_removed = TRUE;")
        self.migrate("on_restart/00_alter-tables.sql")
        for table in tables:
            self.assertEqual(self.query(f"SELECT is_removed FROM {table};"), "t")

    def test_kyc_status_view_requires_kyc_record_and_preserves_other_checks(self):
        self.query(self.orm_ddl())
        self.query("""
            INSERT INTO kyc (id, address) VALUES (1, 'KT1kyc');
            INSERT INTO equiteez_user (id, address)
                SELECT n, 'mv1user' || n FROM generate_series(1, 7) AS n;
            INSERT INTO kyc_registrar (id, kyc_id, user_id) VALUES (1, 1, 7);
            INSERT INTO kyc_member (id, kyc_id, user_id, kyc_registrar_id, expire_at, frozen) VALUES
                (1, 1, 1, NULL, NULL, FALSE),
                (2, 1, 2, 1, NULL, FALSE),
                (3, 1, 3, 1, NOW() + INTERVAL '1 day', FALSE),
                (4, 1, 4, 1, NOW() - INTERVAL '1 day', FALSE),
                (5, 1, 5, 1, NOW() + INTERVAL '1 day', TRUE),
                (6, 1, 6, 1, NOW() + INTERVAL '1 day', FALSE);
            INSERT INTO kyc_blacklisted (kyc_id, user_id) VALUES (1, 6);
        """)
        name = "on_restart/07_create-kyc-member-status-view.sql"
        # Upgrade an existing view with the pre-blacklist column shape.
        old_view = (
            (SQL_ROOT / name)
            .read_text()
            .replace(
                "    END AS is_active,\n    kb.id IS NOT NULL AS is_blacklisted",
                "    END AS is_active",
            )
            .replace("        WHEN km.kyc_registrar_id IS NULL THEN false\n", "")
        )
        self.query(old_view)
        for _ in range(2):
            self.migrate(name)
            self.assertEqual(
                self.query("""
                SELECT kyc_member_id, is_active, is_expired, is_blacklisted
                FROM kyc_member_status_view ORDER BY kyc_member_id;
            """),
                "1|f|f|f\n2|t|f|f\n3|t|f|f\n4|f|t|f\n5|f|f|f\n6|f|f|t",
            )

    def test_fresh_token_discriminator_preserves_allowlist(self):
        self.fixtures(fresh=True)
        self.migrate("on_restart/06_add-token-kind.sql")
        self.migrate("on_restart/06_add-token-kind.sql")
        self.assertEqual(
            self.query("SELECT in_allowlist, is_quote_token FROM token;"), "t|f"
        )

    def test_purchase_snapshots_fresh_orm_schema_and_reindex(self):
        self.query(self.orm_ddl())
        self.migrate("on_reindex/00_create-hypertables.sql")
        # A continuous aggregate with a dependent view keeps this hypertable
        # alive across schema wipe. Reindex must reuse its PK and reinstall
        # the money CHECK without a duplicate-constraint error.
        self.query("""
            CREATE MATERIALIZED VIEW purchase_reindex_daily
            WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 day', timestamp) AS bucket, COUNT(*) AS purchases
                FROM launchpad_purchase_event GROUP BY bucket
            WITH NO DATA;
            CREATE VIEW purchase_reindex_view AS SELECT * FROM purchase_reindex_daily;
        """)
        primary_key = self.query("""
            SELECT oid FROM pg_constraint
            WHERE conrelid='launchpad_purchase_event'::regclass AND contype='p';
        """)
        self.migrate("on_reindex/00_create-hypertables.sql")
        self.assertEqual(
            self.query("""
                SELECT oid FROM pg_constraint
                WHERE conrelid='launchpad_purchase_event'::regclass AND contype='p';
            """),
            primary_key,
        )
        self.assertEqual(
            self.query(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='launchpad_purchase_event' AND column_name IN ('price','total','token_distribution_type') ORDER BY column_name;"
            ),
            "price|numeric|YES\ntoken_distribution_type|smallint|YES\ntotal|numeric|YES",
        )
        self.assertEqual(
            self.query(
                "SELECT COUNT(*) FROM timescaledb_information.hypertables WHERE hypertable_schema=current_schema() AND hypertable_name='launchpad_purchase_event';"
            ),
            "1",
        )
        huge = str(2**256)
        self.query(f"""
            INSERT INTO launchpad(id,address) VALUES (1,'KT1Local');
            INSERT INTO launchpad_launch(id,launchpad_id,name) VALUES (1,1,'Local');
            INSERT INTO launchpad_sale_option(id,launch_id,name) VALUES (1,1,'Starter');
            INSERT INTO equiteez_user(id,address) VALUES (1,'mv1Local');
            INSERT INTO launchpad_purchase_event(timestamp,operation_hash,launch_id,user_id,sale_option_id,payment_name,level,price,total,token_distribution_type,operation_counter,operation_nonce)
                VALUES ('2026-10-16','new',1,1,1,'USDT',1,{huge},{huge},0,7,-1),
                       ('2026-10-16','new',1,1,1,'USDT',1,0,0,1,8,-1),
                       ('2026-10-16','new',1,1,1,'USDT',1,NULL,NULL,NULL,8,0);
        """)
        self.assertEqual(
            self.query(
                "SELECT price::text,total::text FROM launchpad_purchase_event WHERE operation_counter=7;"
            ),
            huge + "|" + huge,
        )
        with self.assertRaisesRegex(AssertionError, "duplicate key value"):
            self.query(
                "INSERT INTO launchpad_purchase_event(timestamp,operation_hash,launch_id,user_id,sale_option_id,payment_name,level,operation_counter) VALUES ('2026-10-16','new',1,1,1,'USDT',1,7);"
            )
        for column in ("price", "total"):
            for invalid in ("-1", "'NaN'"):
                with (
                    self.subTest(column=column, invalid=invalid),
                    self.assertRaisesRegex(AssertionError, "check constraint"),
                ):
                    self.query(
                        f"UPDATE launchpad_purchase_event SET {column}={invalid} WHERE operation_counter=7;"
                    )
        # NUMERIC(78, 0) enforces the digit bound; non-finite infinities overflow.
        for column in ("price", "total"):
            for invalid in (str(10**78), "'Infinity'", "'-Infinity'"):
                with (
                    self.subTest(column=column, invalid=invalid),
                    self.assertRaisesRegex(AssertionError, "numeric field overflow"),
                ):
                    self.query(
                        f"UPDATE launchpad_purchase_event SET {column}={invalid} WHERE operation_counter=7;"
                    )
        with self.assertRaisesRegex(AssertionError, "operation_counter"):
            self.query(
                "INSERT INTO launchpad_purchase_event(timestamp,launch_id,user_id,sale_option_id,payment_name,level) VALUES ('2026-10-16',1,1,1,'USDT',1);"
            )
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM launchpad_purchase_event;"), "3"
        )
        self.migrate("on_reindex/00_create-hypertables.sql")
        self.assertEqual(
            self.query("SELECT COUNT(*) FROM launchpad_purchase_event;"), "0"
        )
        self.assertEqual(self.query("SELECT COUNT(*) FROM purchase_reindex_view;"), "0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
