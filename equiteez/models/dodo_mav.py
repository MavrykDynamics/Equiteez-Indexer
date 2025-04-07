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
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    rwa_orderbook                           = fields.ForeignKeyField('models.Orderbook', related_name='dodo_mavs')
    metadata                                = fields.JSONField(null=True)
    lp_fee                                  = fields.BigIntField(default=0)
    maintainer_fee                          = fields.BigIntField(default=0)
    fee_decimals                            = fields.BigIntField(default=0)
    price_model                             = fields.IntEnumField(enum_type=PriceModel, index=True)
    appraisal_price                         = fields.FloatField(default=0)
    fixed_price_percent                     = fields.BigIntField(default=0)
    orderbook_price_percent                 = fields.BigIntField(default=0)
    quote_token                             = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_tokens')
    base_token                              = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_tokens')
    quote_lp_token                          = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_lp_tokens')
    base_lp_token                           = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_lp_tokens')
    quote_balance                           = fields.FloatField(default=0)
    base_balance                            = fields.FloatField(default=0)
    target_quote_token_amount               = fields.FloatField(default=0)
    target_base_token_amount                = fields.FloatField(default=0)
    quote_balance_limit                     = fields.FloatField(default=0)
    base_balance_limit                      = fields.FloatField(default=0)
    r_status                                = fields.BigIntField(default=0, index=True)
    guide_price                             = fields.FloatField(default=0)
    slippage_factor                         = fields.BigIntField(default=0)

    class Meta:
        table = 'dodo_mav'

class DodoMavLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.DodoMav', related_name='lambdas')

    class Meta:
        table = 'dodo_mav_lambda'

class DodoMavEntrypointStatus(Model, EntrypointStatus):
    contract                                = fields.ForeignKeyField('models.DodoMav', related_name='entrypoint_status')

    class Meta:
        table = 'dodo_mav_entrypoint_status'

class DodoMavHistoryData(Model):
    id                                      = fields.BigIntField(pk=True)
    dodo_mav                                = fields.ForeignKeyField('models.DodoMav', related_name='history_data')
    trader                                  = fields.ForeignKeyField('models.EquiteezUser', related_name='dodo_mav_history_datas')
    timestamp                               = fields.DatetimeField(use_tz=True)
    level                                   = fields.BigIntField()
    type                                    = fields.IntEnumField(enum_type=TradeType, index=True)
    base_token_price                        = fields.FloatField(default=0.0)
    # base_token_price_usd                    = fields.FloatField(null=True)
    base_token_qty                          = fields.FloatField(default=0.0)
    quote_token_qty                         = fields.FloatField(default=0.0)
    base_token_pool                         = fields.FloatField(default=0)
    quote_token_pool                        = fields.FloatField(default=0)
    # lqt_total                               = fields.FloatField(default=0)

    class Meta:
        table = 'dodo_mav_history_data'
