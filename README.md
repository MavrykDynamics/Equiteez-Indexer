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
