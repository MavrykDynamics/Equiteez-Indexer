from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractBase, ContractLambda, EntrypointStatus

###
# Launchpad Enums
###


class LaunchStatus(IntEnum):
    ACTIVE = 0
    INACTIVE = 1
    PAUSED = 2
    CLOSED = 3


class TokenIssuanceType(IntEnum):
    MINT = 0
    TRANSFER = 1


class TokenDistributionType(IntEnum):
    AUTO = 0
    MANUAL = 1


class PurchaseSource(IntEnum):
    USER = 0  # on-chain `purchase` entrypoint
    ADMIN = 1  # off-chain reconciliation via `setPurchaseRecord`


###
# Launchpad Tables
###


class Launchpad(ContractBase):
    """
    Launchpad contract configuration and state.
    Hosts named token launches with per-launch sale options, treasuries, and
    purchase ledgers. Each instance is a singleton sale platform managed by
    a super admin and tied to a single membership KYC contract.
    """

    # Current super admin address
    super_admin = fields.CharField(max_length=36, index=True, null=True)

    # Pending super admin address (2-step rotation)
    new_super_admin = fields.CharField(max_length=36, index=True, null=True)

    # Membership KYC gate
    membership_kyc = fields.ForeignKeyField(
        "models.Kyc", related_name="launchpads", null=True
    )

    # Contract metadata
    metadata = fields.JSONField(null=True)

    class Meta:
        table = "launchpad"


class LaunchpadLambda(Model, ContractLambda):
    """Lambda functions registered on a Launchpad."""

    contract = fields.ForeignKeyField("models.Launchpad", related_name="lambdas")

    class Meta:
        table = "launchpad_lambda"


class LaunchpadEntrypointStatus(Model, EntrypointStatus):
    """Pause status per Launchpad entrypoint."""

    contract = fields.ForeignKeyField(
        "models.Launchpad", related_name="entrypoint_status"
    )

    class Meta:
        table = "launchpad_entrypoint_status"


class LaunchpadTreasury(Model):
    """
    Named treasury addresses on a Launchpad. The `treasuryLedger` is keyed by
    name (e.g. "default"); each name resolves to a destination address that
    receives sale proceeds.
    """

    id = fields.IntField(primary_key=True)

    launchpad = fields.ForeignKeyField("models.Launchpad", related_name="treasuries")

    # Treasury name (key in treasuryLedger)
    name = fields.TextField(index=True)

    # Destination address
    address = fields.CharField(max_length=36, index=True)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_treasury"
        indexes = [
            ("launchpad_id", "name"),
        ]


class LaunchpadLaunch(Model):
    """
    One named token launch on a Launchpad (entry in `launchLedger`).
    Tracks sale schedule, status, cap, total bought, distribution mode,
    and the RWA token being sold.
    """

    id = fields.IntField(primary_key=True)

    launchpad = fields.ForeignKeyField("models.Launchpad", related_name="launches")

    # Launch name (PK part in launchLedger)
    name = fields.TextField(index=True)

    # ACTIVE / INACTIVE / PAUSED / CLOSED
    status = fields.IntEnumField(
        enum_type=LaunchStatus, index=True, default=LaunchStatus.ACTIVE
    )

    # mint / transfer
    token_issuance_type = fields.IntEnumField(
        enum_type=TokenIssuanceType, default=TokenIssuanceType.TRANSFER
    )

    # auto / manual
    token_distribution_type = fields.IntEnumField(
        enum_type=TokenDistributionType, default=TokenDistributionType.AUTO
    )

    # RWA token being sold (FA2 token contract + token_id)
    token = fields.ForeignKeyField(
        "models.Token", related_name="launchpad_launches", null=True
    )

    # Fee percent for purchases (basis points or nat as stored on chain)
    purchase_fee_percent = fields.BigIntField(default=0)

    # Total supply cap for this launch
    max_amount_cap = fields.BigIntField(default=0)

    # Running tally of purchased tokens (all sale options combined)
    total_bought = fields.BigIntField(default=0)

    # Schedule
    sale_start = fields.DatetimeField(null=True)
    sale_end = fields.DatetimeField(null=True)
    sale_closed = fields.DatetimeField(null=True)

    # Convenience flag: true iff any pause entry covers this launch
    is_paused = fields.BooleanField(default=False, index=True)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_launch"
        indexes = [
            ("launchpad_id", "name"),
            ("status",),
        ]


class LaunchpadSaleOption(Model):
    """
    Sale option for a launch (entry in `launch.saleOptions`).
    Defines per-option caps, pause flag, and schedule overrides for one named
    bucket (e.g. "default", "tierA"). Per-tier purchase limits live in
    LaunchpadSaleOptionTier (one row per allowed membership tier).
    """

    id = fields.IntField(primary_key=True)

    launch = fields.ForeignKeyField(
        "models.LaunchpadLaunch", related_name="sale_options"
    )

    # Sale option name (key in saleOptions map)
    name = fields.TextField(index=True)

    # Running tally for this sale option
    total_bought = fields.BigIntField(default=0)

    # Optional global cap (null = unlimited)
    max_amount_cap = fields.BigIntField(null=True)

    is_paused = fields.BooleanField(default=False)

    # Per-option schedule overrides
    sale_start = fields.DatetimeField(null=True)
    sale_end = fields.DatetimeField(null=True)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_sale_option"
        indexes = [
            ("launch_id", "name"),
        ]


class LaunchpadSaleOptionTier(Model):
    """
    Per-tier purchase configuration on a sale option. Mirrors the on-chain
    `allowedMembershipTiers : map(string, tokenSaleUserConfigRecordType)`.
    Each row is a tier (e.g. "tierA", "none" for public) with its own
    minimum-purchase and per-wallet caps; absence of a tier row means that
    tier is not allowed to buy this option.
    """

    id = fields.IntField(primary_key=True)

    sale_option = fields.ForeignKeyField(
        "models.LaunchpadSaleOption", related_name="tiers"
    )

    # Tier name (key in allowedMembershipTiers). "none" denotes public sale.
    name = fields.TextField(index=True)

    # Optional per-tier minimum purchase (null = no minimum)
    min_purchase_amount = fields.BigIntField(null=True)

    # Optional per-tier per-wallet cumulative cap (null = unlimited)
    max_amount_per_wallet_total = fields.BigIntField(null=True)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_sale_option_tier"
        indexes = [
            ("sale_option_id", "name"),
        ]


class LaunchpadSaleOptionPayment(Model):
    """
    Accepted payment for a sale option (entry in `saleOption.payments`).
    Each payment names a currency, a unit price, and the token accepted.
    """

    id = fields.IntField(primary_key=True)

    sale_option = fields.ForeignKeyField(
        "models.LaunchpadSaleOption", related_name="payments"
    )

    # Payment name (key in payments map, e.g. "usdt")
    name = fields.TextField(index=True)

    # Unit price in the payment token's smallest unit
    price = fields.BigIntField(default=0)

    # Token accepted for payment (null until resolved via register_token)
    token = fields.ForeignKeyField(
        "models.Token", related_name="launchpad_payments", null=True
    )

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_sale_option_payment"
        indexes = [
            ("sale_option_id", "name"),
        ]


class LaunchpadPurchase(Model):
    """
    Aggregated purchase record per (launch, user). Mirrors `purchaseLedger`
    keyed by (launchName, address). Sums across all sale options the user
    bought into and tracks distribution progress.
    """

    id = fields.IntField(primary_key=True)

    launch = fields.ForeignKeyField("models.LaunchpadLaunch", related_name="purchases")

    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="launchpad_purchases"
    )

    # Total tokens purchased across all sale options
    total_purchased = fields.BigIntField(default=0)

    # Total tokens already distributed to the user
    total_distributed = fields.BigIntField(default=0)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_purchase"
        indexes = [
            ("launch_id", "user_id"),
        ]


class LaunchpadPurchaseByOption(Model):
    """
    Breakdown of a purchase record by sale option (the `purchased` map inside
    `purchaseRecordType`). Lets us answer "how much did user X buy in tier A".
    """

    id = fields.IntField(primary_key=True)

    purchase = fields.ForeignKeyField(
        "models.LaunchpadPurchase", related_name="by_option"
    )

    sale_option = fields.ForeignKeyField(
        "models.LaunchpadSaleOption", related_name="purchase_breakdowns"
    )

    amount = fields.BigIntField(default=0)

    updated_at = fields.DatetimeField(auto_now=True, index=True)

    class Meta:
        table = "launchpad_purchase_by_option"
        indexes = [
            ("purchase_id", "sale_option_id"),
        ]


class LaunchpadPurchaseEvent(Model):
    """
    Append-only history of individual purchase events (on-chain `purchase`
    entrypoint and admin `setPurchaseRecord` batch). The contract's
    `purchaseLedger` only stores aggregates, so this table is the only
    source for per-transaction purchase analytics.
    """

    id = fields.IntField(primary_key=True)

    launch = fields.ForeignKeyField(
        "models.LaunchpadLaunch", related_name="purchase_events"
    )

    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="launchpad_purchase_events"
    )

    sale_option = fields.ForeignKeyField(
        "models.LaunchpadSaleOption", related_name="purchase_events"
    )

    # Payment name used (key in saleOption.payments)
    payment_name = fields.TextField(index=True)

    # Token accepted for this purchase, if resolvable
    payment_token = fields.ForeignKeyField(
        "models.Token", related_name="launchpad_payment_events", null=True
    )

    # Tokens purchased in this single event
    amount = fields.BigIntField(default=0)

    # USER (on-chain) vs ADMIN (off-chain reconciliation)
    source = fields.IntEnumField(
        enum_type=PurchaseSource, index=True, default=PurchaseSource.USER
    )

    # Mavryk operation hash for traceability
    operation_hash = fields.CharField(max_length=64, index=True, null=True)

    # Position in the parameter batch (0 for single-purchase entrypoint,
    # 0..N-1 for items in a setPurchaseRecord batch). Together with
    # operation_hash, launch, user, sale_option and source forms the dedup
    # key — see unique_together below. Without it, two purchases by the
    # same user in the same option within one admin batch would collide.
    batch_index = fields.IntField(default=0)

    timestamp = fields.DatetimeField(index=True)
    level = fields.BigIntField(index=True)

    class Meta:
        table = "launchpad_purchase_event"
        # Dedup key: prevents duplicate event rows on chain reorg replay.
        # Source is included because purchase (USER) and setPurchaseRecord
        # (ADMIN) can theoretically collide on (op_hash, launch, user, option, 0)
        # if both fire in the same operation (paranoid but cheap).
        unique_together = (
            (
                "operation_hash",
                "launch",
                "user",
                "sale_option",
                "batch_index",
                "source",
            ),
        )
        indexes = [
            ("launch_id", "user_id"),
            ("launch_id", "timestamp"),
        ]


class LaunchpadDistributionEvent(Model):
    """
    Append-only history of token distribution events from
    `distributeTokens`. Each row records one (user, launch) distribution
    within a batch — useful for auditing manual/auto distribution flows.
    """

    id = fields.IntField(primary_key=True)

    launch = fields.ForeignKeyField(
        "models.LaunchpadLaunch", related_name="distribution_events"
    )

    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="launchpad_distribution_events"
    )

    # Tokens distributed in this event
    amount = fields.BigIntField(default=0)

    operation_hash = fields.CharField(max_length=64, index=True, null=True)

    # Position in the distributeTokens parameter batch. See LaunchpadPurchaseEvent
    # for the rationale.
    batch_index = fields.IntField(default=0)

    timestamp = fields.DatetimeField(index=True)
    level = fields.BigIntField(index=True)

    class Meta:
        table = "launchpad_distribution_event"
        # Dedup key: prevents duplicate event rows on chain reorg replay.
        unique_together = (("operation_hash", "launch", "user", "batch_index"),)
        indexes = [
            ("launch_id", "user_id"),
            ("launch_id", "timestamp"),
        ]
