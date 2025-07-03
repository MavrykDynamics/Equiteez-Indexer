from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda, EntrypointStatus

###
# DodoMav Enums
###

class PriceModel(IntEnum):
    FIXED                                   = 0
    DYNAMIC                                 = 1

class TradeType(IntEnum):
    BUY                                     = 0
    SELL                                    = 1

###
# DodoMav Tables
###

class DodoMav(Model):
    """
    DodoMav contract configuration and state.
    This table stores the configuration and current state of DodoMav contracts,
    which provide proactive market making (PMM) functionality for RWA trading.
    DodoMav contracts manage liquidity pools, pricing models, and trading fees
    for specific RWA token pairs.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # DodoMav contract address
    address                                 = fields.CharField(max_length=36, index=True)

    # Current super admin address
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)

    # Pending super admin address
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)

    # Associated RWA orderbook
    rwa_orderbook                           = fields.ForeignKeyField('models.Orderbook', related_name='dodo_mavs')

    # Contract metadata
    metadata                                = fields.JSONField(null=True)

    # Liquidity provider fee
    lp_fee                                  = fields.BigIntField(default=0)

    # Maintainer fee
    maintainer_fee                          = fields.BigIntField(default=0)

    # Fee decimal places
    fee_decimals                            = fields.BigIntField(default=0)

    # Pricing model (FIXED/DYNAMIC)
    price_model                             = fields.IntEnumField(enum_type=PriceModel, index=True)

    # Appraisal price
    appraisal_price                         = fields.FloatField(default=0)

    # Fixed price percentage
    fixed_price_percent                     = fields.BigIntField(default=0)

    # Orderbook price percentage
    orderbook_price_percent                 = fields.BigIntField(default=0)

    # Quote token (e.g., XTZ)
    quote_token                             = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_tokens')

    # Base token (RWA token)
    base_token                              = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_tokens')

    # Quote liquidity provider token
    quote_lp_token                          = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_lp_tokens')

    # Base liquidity provider token
    base_lp_token                           = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_lp_tokens')

    # Current quote token balance
    quote_balance                           = fields.FloatField(default=0)

    # Current base token balance
    base_balance                            = fields.FloatField(default=0)

    # Target quote token amount
    target_quote_token_amount               = fields.FloatField(default=0)

    # Target base token amount
    target_base_token_amount                = fields.FloatField(default=0)

    # Quote token balance limit
    quote_balance_limit                     = fields.FloatField(default=0)

    # Base token balance limit
    base_balance_limit                      = fields.FloatField(default=0)

    # R status (balance indicator)
    r_status                                = fields.BigIntField(default=0, index=True)

    # Guide price for trading
    guide_price                             = fields.FloatField(default=0)

    # Slippage factor
    slippage_factor                         = fields.BigIntField(default=0)

    class Meta:
        table = 'dodo_mav'
        indexes = [
            ("base_token_id",),
            ("quote_token_id",),
            ("base_lp_token_id",),
            ("quote_lp_token_id",),
            ("price_model", "r_status"),
        ]

class DodoMavLambda(Model, ContractLambda):
    """
    Stores lambda functions for a DodoMav contract.
    This table stores lambda functions associated with DodoMav contracts.
    """

    # Reference to DodoMav contract
    contract                                = fields.ForeignKeyField('models.DodoMav', related_name='lambdas')

    class Meta:
        table = 'dodo_mav_lambda'

class DodoMavEntrypointStatus(Model, EntrypointStatus):
    """
    Tracks pause status of DodoMav contract entrypoints.
    This table tracks whether specific entrypoints of DodoMav contracts are paused
    or active.
    """

    # Reference to DodoMav contract
    contract                                = fields.ForeignKeyField('models.DodoMav', related_name='entrypoint_status')

    class Meta:
        table = 'dodo_mav_entrypoint_status'

class DodoMavHistoryData(Model):
    """
    Tracks trading history and pool state changes.
    This table maintains a complete history of all trades and pool state changes
    in DodoMav contracts. Each record captures the trade details, pool balances,
    and pricing information at the time of the trade.
    """

    # Primary key identifier
    id                                      = fields.BigIntField(pk=True)

    # Reference to DodoMav contract
    dodo_mav                                = fields.ForeignKeyField('models.DodoMav', related_name='history_data')

    # User who performed the trade
    trader                                  = fields.ForeignKeyField('models.EquiteezUser', related_name='dodo_mav_history_datas')

    # Trade timestamp
    timestamp                               = fields.DatetimeField()

    # Mavryk blockchain level
    level                                   = fields.BigIntField()

    # Type of trade (BUY/SELL)
    type                                    = fields.IntEnumField(enum_type=TradeType, index=True)

    # Base token price at trade time
    base_token_price                        = fields.FloatField(default=0.0)

    # Base token quantity traded
    base_token_qty                          = fields.FloatField(default=0.0)

    # Quote token quantity traded
    quote_token_qty                         = fields.FloatField(default=0.0)

    # Base token pool balance after trade
    base_token_pool                         = fields.FloatField(default=0)

    # Quote token pool balance after trade
    quote_token_pool                        = fields.FloatField(default=0)

    class Meta:
        table = 'dodo_mav_history_data'
