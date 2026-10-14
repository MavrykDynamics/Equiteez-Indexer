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
