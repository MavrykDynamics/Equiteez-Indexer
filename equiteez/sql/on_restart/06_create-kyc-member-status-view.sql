-- Lives in on_restart on purpose: on_reindex runs only for a fresh schema, so a
-- database migrated in place would keep the pre-blacklist shape of this view.
-- CREATE OR REPLACE VIEW may append columns, which is all the September 2026
-- revision does (is_blacklisted), so it is safe on both paths.
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
    -- Check if member is active (the contract's userIsVerified: not frozen,
    -- not expired, not blacklisted)
    CASE 
        WHEN km.frozen = true THEN false
        WHEN kb.id IS NOT NULL THEN false
        WHEN km.expire_at IS NULL THEN true
        WHEN km.expire_at < NOW() THEN false
        ELSE true
    END AS is_active,
    kb.id IS NOT NULL AS is_blacklisted
FROM 
    kyc_member km
    JOIN kyc k ON km.kyc_id = k.id
    JOIN equiteez_user eu ON km.user_id = eu.id
    LEFT JOIN kyc_blacklisted kb ON kb.kyc_id = km.kyc_id AND kb.user_id = km.user_id;
