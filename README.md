## Equiteez Indexer

### Token allowlist filters

`token.in_allowlist` includes contracts in either `base_tokens` or `quote_tokens`.
To list RWA assets, filter on both `in_allowlist = true` and
`is_quote_token = false`; quote-token lists use `is_quote_token = true`.
Classification is per contract address, including every FA2 token ID. If an
address appears in both lists, it is classified as a quote token.

Restarting the indexer adds `is_quote_token` to an existing database and refreshes
both flags from `CONTRACT_ALLOWLIST_URL`. On the first upgrade, existing allowlist
flags are cleared until a successful refresh can classify them. If the endpoint
is unavailable, the scheduled allowlist job retries; later fetch failures preserve
the last known classification. Reconfigure Hasura to expose the new column before
updating consumer filters.

For an existing database using the local `schema_modified: wipe` policy, run
`dipdup -c dipdup.local.yml -c dipdup.contracts.yml -c dipdup.types.yml -c dipdup.yml schema approve`
before starting this version to retain indexed data. The production configuration
uses `schema_modified: ignore`, so the restart migration runs in place.

### KYC removals and incremental synchronization

`kyc_registrar_admin`, `kyc_membership_tier`, `kyc_membership`, and
`kyc_membership_tier_discount` keep removed entries with `is_removed = true`.
Removal advances `updated_at`; adding the same entry again reuses its ID and
clears `is_removed`. Queries for current state must filter `is_removed = false`.
DualCursor consumers must fetch removed rows too, so they can remove those IDs
from their local state. `kyc_member.membership_tier` ignores removed memberships,
and `kyc_member_status_view.is_active` is false after the KYC record is removed.

The restart migration adds these flags to existing tables with a default of
`false`. Reconfigure Hasura to expose the columns before updating consumers.
Rows hard-deleted by an earlier version cannot be recovered by this migration;
reindex and rebuild downstream state if historical removals need to be restored.


### Launch purchase snapshots

`launchpad_purchase_event` now records nullable `price`, `total`, and
`token_distribution_type` when an event is first inserted. Price is read from
the selected payment in the operation's launch-ledger diff; it is not joined
from mutable sale settings later. Mode is `0` (AUTO), `1` (MANUAL), or null.
Money uses the built-in DipDup `DecimalField(max_digits=78, decimal_places=0)`
and PostgreSQL `NUMERIC(78,0)`: exact integers from 0 to `10^78 - 1`. There is no
custom ORM field or field-registry patch. Both local and production configs set
`advanced.decimal_precision: 78` explicitly because this pinned DipDup fork does
not infer precision for its DecimalField. Keep that setting in custom configs.
Contract values and receipt arithmetic use Python integers; no floating-point
conversion is involved. Values beyond 78 digits are unsupported and fail instead
of being truncated. `distribution_date` is not part of this contract.

For USER purchases, total is attributed from applied MvKT internal operations
for the exact hash/counter. The parser checks currency contract, FA2 token ID,
buyer, treasuries, issuance, and the complete per-purchase operation groups.
It uses MvKT execution IDs, not creation nonces, for operation order. The
supported launchpad emits optional issuance, net payment, then optional paid
fee; permit helpers retain action order. Net-payment validation uses the
contract's fixed quantity scale of 1,000,000 and fee basis points. The actual
paid fee comes from the receipt, without fetching current KYC discounts.

A receipt group is fetched from the existing configured MvKT datasource and
cached for the most recent block/hash only. Historical DipDup REST operations
without a block hash are not cached and must match the indexed inputs/diffs.
Batch items share one validated receipt. Empty, incomplete or mismatched receipts
are fetched up to five times, with 0.5, 1, 2 and 4 second delays, to tolerate REST
lag behind the websocket feed. Only a validated receipt is cached. HTTP transport
failures use the datasource's existing retry policy. If either retry budget is
exhausted, the handler fails without recording a purchase; DipDup must be restarted
after the upstream problem is resolved. This avoids permanently recording unknown money.
Unmatched or ambiguous effects, unknown treasuries, and nested launchpad calls
retain the purchase with `total = null` and a diagnostic reason. Unsupported
contract variants must be checked against their receipts before claiming
financial coverage. Native-MAV permits are not supported by this contract.

ADMIN records have null price/total because registration does not prove a
payment. Mode can still be recorded, but AUTO on an ADMIN record does not prove
that tokens were delivered. Replaying an indexed purchase preserves its ID
and snapshots.

This release requires a **new, empty database and full reindex**. The ORM creates
the snapshot columns and the call-coordinate dedup key; `on_reindex` creates the
purchase hypertable and enforces nonnegative integral money. No in-place upgrade
or legacy purchase-row compatibility is provided. Subsequent `schema wipe` and
reindex runs on this schema also support a surviving purchase hypertable, keeping
its primary key and recreating the money constraint. `operation_counter` is required;
`operation_nonce = -1` denotes a direct transaction without an internal nonce.

Keep relayer publication paused during the reindex and coordinate its cursor
and dedup state with the replacement database before resuming. Deploy the notifier
and RWA backend allow-lists before publishing enriched events. Existing inbox
history is not automatically rewritten by reindexing.

Tests: `python -m unittest tests.test_launchpad_purchase_snapshots -v` covers
payment attribution, snapshots and replay. Set `PURCHASE_TEST_DATABASE_URL` to a
test PostgreSQL URL to also check exact large-value persistence and delete/update
rollback through `10^78 - 1`; CI always runs this mode. Each test creates and drops
its own uniquely named schema. Without this variable, SQLite runs the smaller
snapshot cases and skips the large-value test: the pinned fork's SQLite numeric
affinity cannot preserve large decimals. The
public Basenet receipt fixture was fetched on 2026-10-16 from
`/v1/operations/transactions/onjMSdMd27kQR5fAfnEtg5xD9CMdXBkCxTGbg6uSWNVqSH6AUEk`:
1.37 units at a price of 30, paid 40.689 + 0.411 = 41.1 (six payment decimals).
Other payment/batch fixtures are synthetic and follow the local contract's
operation shapes. `RUN_MIGRATION_TESTS=1 python tests/test_review_migrations.py`
checks purchase constraints on a fresh schema and repeated reindex with dependent
continuous aggregates/views, plus the existing unrelated migrations
using an isolated TimescaleDB database. No live balances or notifications are modified by tests.
