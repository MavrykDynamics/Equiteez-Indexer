from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda

###
# DodoMav Enums
###

class PriceModel(IntEnum):
    FIXED                                   = 0
    DYNAMIC                                 = 1

###
# DodoMav Tables
###

class DodoMav(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    rwa_orderbook                           = fields.ForeignKeyField('models.Orderbook', related_name='dodo_mavs')
    metadata                                = fields.JSONField(null=True)
    lp_fee                                  = fields.BigIntField(default=0)
    maintainer_fee                          = fields.BigIntField(default=0)
    fee_decimals                            = fields.BigIntField(default=0)
    price_model                             = fields.IntEnumField(enum_type=PriceModel, index=True)
    appraisal_price                         = fields.BigIntField(default=0)
    fixed_price_percent                     = fields.BigIntField(default=0)
    orderbook_price_percent                 = fields.BigIntField(default=0)
    quote_token                             = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_tokens')
    base_token                              = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_tokens')
    quote_lp_token                          = fields.ForeignKeyField('models.Token', related_name='dodo_mav_quote_lp_tokens')
    base_lp_token                           = fields.ForeignKeyField('models.Token', related_name='dodo_mav_base_lp_tokens')
    quote_balance                           = fields.BigIntField(default=0)
    base_balance                            = fields.BigIntField(default=0)
    target_quote_token_amount               = fields.BigIntField(default=0)
    target_base_token_amount                = fields.BigIntField(default=0)
    quote_balance_limit                     = fields.BigIntField(default=0)
    base_balance_limit                      = fields.BigIntField(default=0)
    r_status                                = fields.BigIntField(default=0)
    guide_price                             = fields.BigIntField(default=0)
    slippage_factor                         = fields.BigIntField(default=0)

    class Meta:
        table = 'dodo_mav'

class DodoMavLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.DodoMav', related_name='lambdas')

    class Meta:
        table = 'dodo_mav_lambda'

class DodoMavPause(Model):
    id                                      = fields.IntField(primary_key=True)
    dodo_mav                                = fields.ForeignKeyField('models.DodoMav', related_name='pause_ledger')
    entrypoint                              = fields.TextField(index=True)
    paused                                  = fields.BooleanField(default=False)

    class Meta:
        table = 'dodo_mav_pause'
