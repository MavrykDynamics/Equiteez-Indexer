-- Progress % for a launch: total_bought / max_amount_cap, rounded to 2 decimals.
CREATE OR REPLACE FUNCTION launchpad_launch_progress_percent(l launchpad_launch)
    RETURNS numeric
    LANGUAGE sql STABLE AS $$
    SELECT CASE
        WHEN l.max_amount_cap > 0
        THEN ROUND(l.total_bought::numeric / l.max_amount_cap::numeric * 100, 2)
        ELSE 0
    END;
$$;

-- Progress % for a sale option.
CREATE OR REPLACE FUNCTION launchpad_sale_option_progress_percent(so launchpad_sale_option)
    RETURNS numeric
    LANGUAGE sql STABLE AS $$
    SELECT CASE
        WHEN so.max_amount_cap IS NOT NULL AND so.max_amount_cap > 0
        THEN ROUND(so.total_bought::numeric / so.max_amount_cap::numeric * 100, 2)
        ELSE NULL
    END;
$$;

-- Tokens purchased but not yet distributed to the user, for a single
-- (user, launch) row.
CREATE OR REPLACE FUNCTION launchpad_purchase_pending_distribution(p launchpad_purchase)
    RETURNS bigint
    LANGUAGE sql STABLE AS $$
    SELECT GREATEST(0, p.total_purchased - p.total_distributed);
$$;
