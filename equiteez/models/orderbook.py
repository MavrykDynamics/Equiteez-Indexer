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
    """
    Orderbook contract configuration and state.
    This table stores the configuration and current state of orderbook contracts
    for RWA trading. Orderbooks manage buy and sell orders,
    track prices, fees, and order statistics for specific RWA tokens.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Orderbook contract address
    address                                 = fields.CharField(max_length=36, index=True)

    # Current super admin address
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)

    # Pending super admin address
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)

    # RWA token being traded
    rwa_token                               = fields.ForeignKeyField('models.Token', related_name='orderbooks', null=True)

    # Associated KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='orderbooks', null=True)

    # Contract metadata
    metadata                                = fields.JSONField(null=True)

    # Minimum order expiry time (seconds)
    min_expiry_time                         = fields.BigIntField(default=0)

    # Minimum time before order can be closed
    min_time_before_closing_order           = fields.BigIntField(default=0)

    # Minimum buy order amount
    min_buy_order_amount                    = fields.BigIntField(default=0)

    # Minimum buy order value
    min_buy_order_value                     = fields.BigIntField(default=0)

    # Minimum sell order amount
    min_sell_order_amount                   = fields.BigIntField(default=0)

    # Minimum sell order value
    min_sell_order_value                    = fields.BigIntField(default=0)

    # Fee for buy orders
    buy_order_fee                           = fields.BigIntField(default=0)

    # Fee for sell orders
    sell_order_fee                          = fields.BigIntField(default=0)

    # ID of highest buy price order
    highest_buy_price_order_id              = fields.BigIntField(default=0)

    # Highest buy price
    highest_buy_price                       = fields.BigIntField(default=0)

    # ID of lowest sell price order
    lowest_sell_price_order_id              = fields.BigIntField(default=0)

    # Lowest sell price
    lowest_sell_price                       = fields.BigIntField(default=0)

    # Last matched order price
    last_matched_price                      = fields.BigIntField(default=0)

    # Timestamp of last matched price
    last_matched_price_timestamp            = fields.TimeField(null=True)

    # Counter for buy orders
    buy_order_counter                       = fields.BigIntField(default=0)

    # Counter for sell orders
    sell_order_counter                      = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook'
        indexes = [
            ("rwa_token_id",),
        ]

class OrderbookLambda(Model, ContractLambda):
    """
    Stores lambda functions for an orderbook contract.
    This table stores lambda functions associated with orderbook contracts.
    """

    # Reference to orderbook contract
    contract                                = fields.ForeignKeyField('models.Orderbook', related_name='lambdas')

    class Meta:
        table = 'orderbook_lambda'

class OrderbookEntrypointStatus(Model, EntrypointStatus):
    """
    Tracks pause status of orderbook contract entrypoints.
    
    This table tracks whether specific entrypoints of orderbook contracts are paused
    or active.
    """

    # Reference to orderbook contract
    contract                                = fields.ForeignKeyField('models.Orderbook', related_name='entrypoint_status')

    class Meta:
        table = 'orderbook_entrypoint_status'

class OrderbookCurrency(Model):
    """
    Defines currencies accepted by orderbooks.    
    This table stores the currencies that are accepted for trading in orderbooks,
    including both native tokens and external tokens.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to orderbook contract
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='currencies')

    # Token associated with this currency
    token                                   = fields.ForeignKeyField('models.Token', related_name='orderbook_currencies', null=True)

    # Name of the currency
    currency_name                           = fields.TextField(index=True)

    class Meta:
        table = 'orderbook_currency'
        indexes = [
            ("orderbook_id", "token_id"),
        ]

class OrderbookFee(Model):
    """
    Tracks fees collected by orderbooks.
    This table stores information about fees collected by orderbooks for trading
    operations, including fee amounts and payment status.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to orderbook contract
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='fees')

    # Currency used for the fee
    currency                                = fields.ForeignKeyField('models.OrderbookCurrency', related_name='fees')

    # Token related to the fee
    related_token                           = fields.ForeignKeyField('models.Token', related_name='orderbook_fees', null=True)

    # Fee amount
    fee_amount                              = fields.BigIntField(default=0)

    # Amount of fee that has been paid
    paid_fee                                = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_fee'

class OrderbookRwaOrder(Model):
    """
    Associates RWA tokens with orderbooks.
    This table creates the relationship between RWA tokens and orderbooks,
    allowing specific tokens to be traded in specific orderbooks.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to orderbook contract
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='rwa_orders')

    # RWA token being traded
    rwa_token                               = fields.ForeignKeyField('models.Token', related_name='orderbook_rwa_orders')

    class Meta:
        table = 'orderbook_rwa_order'
        indexes = [
            ("orderbook_id", "rwa_token_id"),
        ]

class OrderbookRwaOrderBuyPrice(Model):
    """
    Tracks buy prices for RWA orders.
    This table stores buy price levels for RWA orders, including the number
    of orders at each price level.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to RWA order
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_buy_prices')

    # Number of orders at this price level
    counter                                 = fields.BigIntField(default=0)

    # Buy price level
    price                                   = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_rwa_order_buy_price'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderSellPrice(Model):
    """
    Tracks sell prices for RWA orders.    
    This table stores sell price levels for RWA orders, including the number
    of orders at each price level.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to RWA order
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_sell_prices')

    # Number of orders at this price level
    counter                                 = fields.BigIntField(default=0)

    # Sell price level
    price                                   = fields.BigIntField(default=0)

    class Meta:
        table = 'orderbook_rwa_order_sell_price'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderPrice():
    """
    Abstract base class for RWA order prices.    
    This class provides common fields for tracking order prices and associated
    order IDs in the orderbook system.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Array of order IDs at this price level
    order_ids                               = fields.ArrayField(element_type="INT", null=True)

    # Price level
    price                                   = fields.BigIntField(default=0)

class OrderbookRwaOrderBuyOrder(Model, OrderbookRwaOrderPrice):
    """
    Stores buy orders for RWA tokens at specific price levels.
    This table stores buy orders grouped by price level, allowing efficient
    order matching and price discovery.
    """

    # Reference to RWA order
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_buy_orders')

    class Meta:
        table = 'orderbook_rwa_order_buy_order'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookRwaOrderSellOrder(Model, OrderbookRwaOrderPrice):
    """
    Stores sell orders for RWA tokens at specific price levels.    
    This table stores sell orders grouped by price level, allowing efficient
    order matching and price discovery.
    """

    # Reference to RWA order
    rwa_order                               = fields.ForeignKeyField('models.OrderbookRwaOrder', related_name='orderbook_rwa_order_sell_orders')

    class Meta:
        table = 'orderbook_rwa_order_sell_order'
        indexes = [
            ("rwa_order_id", "price"),
        ]

class OrderbookOrder(Model):
    """
    Main table storing all orders in the orderbook.
    This table stores all buy and sell orders placed in orderbooks for RWA trading.
    Each order tracks the amount, price, fulfillment status, and timing information.
    Orders can be fulfilled, canceled, expired, or refunded based on market conditions.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to orderbook contract
    orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='orders')

    # Unique order identifier
    order_id                                = fields.BigIntField(default=0, index=True)

    # Type of order (BUY/SELL)
    order_type                              = fields.IntEnumField(enum_type=OrderType, index=True)

    # User who placed the order
    initiator                               = fields.ForeignKeyField('models.EquiteezUser', related_name='orderbook_orders')

    # Order currency
    currency                                = fields.ForeignKeyField('models.OrderbookCurrency', related_name='orders')

    # Amount of RWA tokens
    rwa_token_amount                        = fields.BigIntField(default=0)

    # Price per RWA token
    price_per_rwa_token                     = fields.BigIntField(default=0, index=True)

    # Amount that has been fulfilled
    fulfilled_amount                        = fields.BigIntField(default=0)

    # Amount remaining to be fulfilled
    unfulfilled_amount                      = fields.BigIntField(default=0)

    # Total amount paid out
    total_paid_out                          = fields.BigIntField(default=0)

    # USD value of RWA token amount
    total_usd_value_of_rwa_token_amount     = fields.BigIntField(default=0)

    # Whether order is completely fulfilled
    is_fulfilled                            = fields.BooleanField(default=False, index=True)

    # Whether order has been canceled
    is_canceled                             = fields.BooleanField(default=False, index=True)

    # Whether order has expired
    is_expired                              = fields.BooleanField(default=False, index=True)

    # Whether order has been refunded
    is_refunded                             = fields.BooleanField(default=False)

    # Amount refunded
    refunded_amount                         = fields.BigIntField(default=0)

    # Order expiry timestamp
    order_expiry                            = fields.DatetimeField(null=True, index=True)

    # Order creation timestamp
    created_at                              = fields.DatetimeField(null=True, index=True)

    # Order completion timestamp
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

# class OrderbookHistoryData(Model):
#     id                                      = fields.BigIntField(pk=True)
#     orderbook                               = fields.ForeignKeyField('models.Orderbook', related_name='history_data')
#     order                                   = fields.ForeignKeyField('models.OrderbookOrder', related_name='history_data')
#     trader                                  = fields.ForeignKeyField('models.EquiteezUser', related_name='orderbook_history_data')
#     timestamp                               = fields.DatetimeField()
#     level                                   = fields.BigIntField()
#     token_price                             = fields.FloatField(default=0.0)
#     token_price_usd                         = fields.FloatField(null=True)
#     token0_qty                              = fields.FloatField(default=0.0)
#     token1_qty                              = fields.FloatField(default=0.0)
#     token0_pool                             = fields.BigIntField(default=0)
#     token1_pool                             = fields.BigIntField(default=0)
#     lqt_total                               = fields.BigIntField(default=0)

#     class Meta:
#         table = 'orderbook_history_data'
