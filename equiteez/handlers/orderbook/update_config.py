from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.update_config import UpdateConfigParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, OrderbookStorage],
) -> None:
    # Fetch operations info
    address                         = update_config.data.target_address
    min_expiry_time                 = update_config.storage.config.minExpiryTime
    min_time_before_closing_order   = update_config.storage.config.minTimeBeforeClosingOrder
    min_buy_order_amount            = update_config.storage.config.minBuyOrderAmount
    min_buy_order_value             = update_config.storage.config.minBuyOrderValue
    min_sell_order_amount           = update_config.storage.config.minSellOrderAmount
    min_sell_order_value            = update_config.storage.config.minSellOrderValue
    buy_order_fee                   = update_config.storage.config.buyOrderFee
    sell_order_fee                  = update_config.storage.config.sellOrderFee

    # Get orderbook
    orderbook       = await models.Orderbook.get(
        address = address
    )

    # Update record
    orderbook.min_expiry_time                   = min_expiry_time
    orderbook.min_time_before_closing_order     = min_time_before_closing_order
    orderbook.min_buy_order_amount              = min_buy_order_amount
    orderbook.min_buy_order_value               = min_buy_order_value
    orderbook.min_sell_order_amount             = min_sell_order_amount
    orderbook.min_sell_order_value              = min_sell_order_value
    orderbook.buy_order_fee                     = buy_order_fee
    orderbook.sell_order_fee                    = sell_order_fee
    await orderbook.save()
