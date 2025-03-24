from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda, EntrypointStatus

###
# Orderbook Enums
###

class OrderType(IntEnum):
    BUY                                     = 0
    SELL                                    = 1

###
# Orderbook Tables
###

class Orderbook(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    rwa_token                               = fields.ForeignKeyField('models.Token', related_name='orderbooks', null=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='orderbooks', null=True)
    metadata                                = fields.JSONField(null=True)
    min_expiry_time                         = fields.BigIntField(default=0)
    min_time_before_closing_order           = fields.BigIntField(default=0)
    min_buy_order_amount                    = fields.BigIntField(default=0)
    min_buy_order_value                     = fields.BigIntField(default=0)
    min_sell_order_amount                   = fields.BigIntField(default=0)
    min_sell_order_value                    = fields.BigIntField(default=0)
    buy_order_fee                           = fields.BigIntField(default=0)
    sell_order_fee                          = fields.BigIntField(default=0)
    highest_buy_price_order_id              = fields.BigIntField(default=0)
    highest_buy_price                       = fields.BigIntField(default=0)
    lowest_sell_price_order_id              = fields.BigIntField(default=0)
    lowest_sell_price                       = fields.BigIntField(default=0)
    last_matched_price                      = fields.BigIntField(default=0)
    last_matched_price_timestamp            = fields.TimeField(null=True)
    buy_order_counter                       = fields.BigIntField(default=0)
    sell_order_counter                      = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook'
        indexes = [
            ("rwa_token_id",),
        ]

class OrderbookLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.Orderbook', related_name='lambdas')

    class Meta:
        table = 'orderbook_lambda'

class OrderbookEntrypointStatus(Model, EntrypointStatus):
    contract                                = fields.ForeignKeyField('models.Orderbook', related_name='entrypoint_status')

    class Meta:
        table = 'orderbook_entrypoint_status'

class OrderbookCurrency(Model):
    id                                      = fields.IntField(primary_key=True)
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='currencies')
    token                                   = fields.ForeignKeyField('models.Token', related_name='orderbook_currencies', null=True)
    currency_name                           = fields.TextField(index=True)

    class Meta:
        table = 'orderbook_currency'
        indexes = [
            ("orderbook_id", "token_id"),
        ]

class OrderbookFee(Model):
    id                                      = fields.IntField(primary_key=True)
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='fees')
    currency                                = fields.ForeignKeyField('models.OrderbookCurrency', related_name='fees')
    related_token                           = fields.ForeignKeyField('models.Token', related_name='orderbook_fees', null=True)
    fee_amount                              = fields.BigIntField(default=0)
    paid_fee                                = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_fee'

class OrderbookRwaOrder(Model):
    id                                      = fields.IntField(primary_key=True)
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='rwa_orders')
    rwa_token                               = fields.ForeignKeyField('models.Token', related_name='orderbook_rwa_orders')

    class Meta:
        table = 'orderbook_rwa_order'
        indexes = [
            ("orderbook_id", "rwa_token_id"),
        ]

class OrderbookRwaOrderBuyPrice(Model):
    id                                      = fields.IntField(primary_key=True)
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_buy_prices')
    counter                                 = fields.BigIntField(default=0)
    price                                   = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_rwa_order_buy_price'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderSellPrice(Model):
    id                                      = fields.IntField(primary_key=True)
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_sell_prices')
    counter                                 = fields.BigIntField(default=0)
    price                                   = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_rwa_order_sell_price'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderPrice():
    id                                      = fields.IntField(primary_key=True)
    order_ids                               = fields.ArrayField(null=True)
    price                                   = fields.BigIntField(default=0)

class OrderbookRwaOrderBuyOrder(Model, OrderbookRwaOrderPrice):
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_buy_orders')

    class Meta:
        table = 'orderbook_rwa_order_buy_order'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderSellOrder(Model, OrderbookRwaOrderPrice):
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_sell_orders')

    class Meta:
        table = 'orderbook_rwa_order_sell_order'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookOrder(Model):
    id                                      = fields.IntField(primary_key=True)
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='orders')
    order_id                                = fields.BigIntField(default=0, index=True)  # Added index
    order_type                              = fields.IntEnumField(enum_type=OrderType, index=True)
    initiator                               = fields.ForeignKeyField('models.EquiteezUser', related_name='orderbook_orders')
    currency                                = fields.ForeignKeyField('models.OrderbookCurrency', related_name='orders')
    rwa_token_amount                        = fields.BigIntField(default=0)
    price_per_rwa_token                     = fields.BigIntField(default=0, index=True)  # Added index
    fulfilled_amount                        = fields.BigIntField(default=0)
    unfulfilled_amount                      = fields.BigIntField(default=0)
    total_paid_out                          = fields.BigIntField(default=0)
    total_usd_value_of_rwa_token_amount     = fields.BigIntField(default=0)
    is_fulfilled                            = fields.BooleanField(default=False, index=True)  # Added index
    is_canceled                             = fields.BooleanField(default=False, index=True)  # Added index
    is_expired                              = fields.BooleanField(default=False, index=True)  # Added index
    is_refunded                             = fields.BooleanField(default=False)
    refunded_amount                         = fields.BigIntField(default=0)
    order_expiry                            = fields.DatetimeField(null=True, index=True)  # Added index
    created_at                              = fields.DatetimeField(null=True, index=True)  # Added index
    ended_at                                = fields.DatetimeField(null=True)

    class Meta:
        table = 'orderbook_order'
        indexes = [
            ("orderbook_id", "order_id"),
            ("orderbook_id", "order_type"),
            ("orderbook_id", "initiator"),
            ("orderbook_id", "is_fulfilled", "is_canceled", "is_expired"),
            ("created_at", "order_expiry"),
        ]
