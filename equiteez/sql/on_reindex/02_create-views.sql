CREATE OR REPLACE VIEW kyc_member_status_view AS
SELECT 
    km.id AS kyc_member_id,
    km.kyc_id,
    k.address AS kyc_address,
    eu.id AS user_id,
    eu.address AS user_address,
    km.kyc_registrar_id,
    km.country,
    km.region,
    km.investor_type,
    km.expire_at,
    km.frozen,
    -- Check if member is expired
    CASE 
        WHEN km.expire_at IS NULL THEN false
        WHEN km.expire_at < NOW() THEN true
        ELSE false
    END AS is_expired,
    -- Check if member is active
    CASE 
        WHEN km.frozen = true THEN false
        WHEN km.expire_at IS NULL THEN true
        WHEN km.expire_at < NOW() THEN false
        ELSE true
    END AS is_active
FROM 
    kyc_member km
    JOIN kyc k ON km.kyc_id = k.id
    JOIN equiteez_user eu ON km.user_id = eu.id;

CREATE OR REPLACE VIEW token_metadata_view AS
SELECT 
    t.id AS token_id,
    t.address,
    t.token_id AS token_number,
    t.token_standard,
    t.metadata,
    t.token_metadata,
    -- Extract common token metadata fields for faster access
    (t.token_metadata->>'name')::text AS name,
    (t.token_metadata->>'symbol')::text AS symbol,
    (t.token_metadata->>'decimals')::text AS decimals,
    (t.token_metadata->>'thumbnailUri')::text AS thumbnail_uri,
    (t.token_metadata->>'description')::text AS description,
    (t.token_metadata->>'artifactUri')::text AS artifact_uri
FROM 
    token t;

CREATE OR REPLACE VIEW orderbook_summary_view AS
SELECT 
    o.id AS orderbook_id,
    o.address AS orderbook_address,
    o.last_matched_price,
    o.last_matched_price_timestamp,
    o.highest_buy_price,
    o.lowest_sell_price,
    rwt.address AS rwa_token_address,
    rwt.token_id AS rwa_token_id,
    rwt.token_metadata AS rwa_token_metadata,
    -- Active order counts
    COUNT(DISTINCT CASE WHEN oo.order_type = 0 AND oo.is_fulfilled = false AND 
                         oo.is_canceled = false AND oo.is_expired = false 
                    THEN oo.id END) AS active_buy_orders_count,
    COUNT(DISTINCT CASE WHEN oo.order_type = 1 AND oo.is_fulfilled = false AND 
                         oo.is_canceled = false AND oo.is_expired = false 
                    THEN oo.id END) AS active_sell_orders_count,
    -- Total volume in last 24 hours (fulfilled amounts)
    SUM(CASE WHEN oo.created_at >= NOW() - INTERVAL '24 hours' THEN oo.fulfilled_amount ELSE 0 END) AS volume_24h
FROM 
    orderbook o
    LEFT JOIN token rwt ON o.rwa_token_id = rwt.id
    LEFT JOIN orderbook_order oo ON o.id = oo.orderbook_id
GROUP BY 
    o.id, o.address, rwt.address, rwt.token_id, rwt.token_metadata;

-- Token holder count view
CREATE OR REPLACE VIEW token_holders_view AS
SELECT 
    t.id AS token_id,
    t.address AS token_address,
    t.token_id AS token_number,
    COUNT(DISTINCT eub.user_id) AS holder_count,
    SUM(eub.balance) AS total_supply
FROM 
    token t
    LEFT JOIN equiteez_user_balance eub ON t.id = eub.token_id
WHERE 
    eub.balance > 0
GROUP BY 
    t.id, t.address, t.token_id;

-- User's active orders summary view
CREATE OR REPLACE VIEW user_orders_summary_view AS
SELECT 
    eu.address AS user_address,
    o.id AS orderbook_id,
    o.address AS orderbook_address,
    -- Buy orders counts
    COUNT(DISTINCT CASE WHEN oo.order_type = 0 AND oo.is_fulfilled = false AND 
                         oo.is_canceled = false AND oo.is_expired = false 
                    THEN oo.id END) AS active_buy_orders_count,
    -- Sell orders counts
    COUNT(DISTINCT CASE WHEN oo.order_type = 1 AND oo.is_fulfilled = false AND 
                         oo.is_canceled = false AND oo.is_expired = false 
                    THEN oo.id END) AS active_sell_orders_count,
    -- Total buy volume
    SUM(CASE WHEN oo.order_type = 0 THEN oo.rwa_token_amount ELSE 0 END) AS total_buy_volume,
    -- Total sell volume
    SUM(CASE WHEN oo.order_type = 1 THEN oo.rwa_token_amount ELSE 0 END) AS total_sell_volume
FROM 
    equiteez_user eu
    JOIN orderbook_order oo ON eu.id = oo.initiator_id
    JOIN orderbook o ON oo.orderbook_id = o.id
GROUP BY 
    eu.id, eu.address, o.id, o.address;
