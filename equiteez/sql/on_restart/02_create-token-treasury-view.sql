-- Maps an RWA token to its launchTreasury address(es)

CREATE OR REPLACE VIEW token_launch_treasury AS
SELECT DISTINCT
    l.token_id,
    tr.address AS treasury_address
FROM launchpad_launch l
JOIN launchpad_treasury tr ON tr.launchpad_id = l.launchpad_id
WHERE tr.name = 'launchTreasury'
  AND l.token_id IS NOT NULL;
