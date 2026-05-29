-- Launchpad time-series wrappers. Hasura tracks these (not the continuous
-- aggregates directly) — wraps the bucket column as a stable `timestamp`.
--
-- Must run after 06_create-launchpad-rollups.sql which creates the underlying
-- continuous aggregates. Hence the separate file (02_create-views.sql runs
-- before 06).
CREATE OR REPLACE VIEW launchpad_purchase_stats_1h_view AS
SELECT bucket AS timestamp, launch_id, purchase_count, unique_buyers, total_amount, avg_amount
FROM launchpad_purchase_stats_1h;

CREATE OR REPLACE VIEW launchpad_purchase_stats_1d_view AS
SELECT bucket AS timestamp, launch_id, purchase_count, unique_buyers, total_amount, avg_amount
FROM launchpad_purchase_stats_1d;

CREATE OR REPLACE VIEW launchpad_purchase_stats_1w_view AS
SELECT bucket AS timestamp, launch_id, purchase_count, unique_buyers, total_amount, avg_amount
FROM launchpad_purchase_stats_1w;
