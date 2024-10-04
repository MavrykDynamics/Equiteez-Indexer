from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import get_contract_metadata, register_token
from dateutil import parser 

async def origination(
    ctx: HandlerContext,
    orderbook_origination: TezosOrigination[OrderbookStorage],
) -> None:
    # Fetch operation info
    address = orderbook_origination.data.originated_contract_address
    super_admin                     = orderbook_origination.storage.superAdmin
    new_super_admin                 = orderbook_origination.storage.newSuperAdmin
    rwa_token_address               = orderbook_origination.storage.rwaTokenAddress
    kyc_address                     = orderbook_origination.storage.kycAddress
    min_expiry_time                 = orderbook_origination.storage.config.minExpiryTime
    min_time_before_closing_order   = orderbook_origination.storage.config.minTimeBeforeClosingOrder
    min_buy_order_amount            = orderbook_origination.storage.config.minBuyOrderAmount
    min_buy_order_value             = orderbook_origination.storage.config.minBuyOrderValue
    min_sell_order_amount           = orderbook_origination.storage.config.minSellOrderAmount
    min_sell_order_value            = orderbook_origination.storage.config.minSellOrderValue
    buy_order_fee                   = orderbook_origination.storage.config.buyOrderFee
    sell_order_fee                  = orderbook_origination.storage.config.sellOrderFee
    place_buy_order_is_paused       = orderbook_origination.storage.breakGlassConfig.placeBuyOrderIsPaused
    place_sell_order_is_paused      = orderbook_origination.storage.breakGlassConfig.placeSellOrderIsPaused
    cancel_orders_is_paused         = orderbook_origination.storage.breakGlassConfig.cancelOrdersIsPaused
    highest_buy_price_order_id      = orderbook_origination.storage.highestBuyPrice.orderId
    highest_buy_price               = orderbook_origination.storage.highestBuyPrice.price
    lowest_sell_price_order_id      = orderbook_origination.storage.lowestSellPrice.orderId
    lowest_sell_price               = orderbook_origination.storage.lowestSellPrice.price
    last_matched_price              = orderbook_origination.storage.lastMatchedPrice.price
    last_matched_price_timestamp    = parser.parse(orderbook_origination.storage.lastMatchedPrice.lastMatchedTimestamp)
    buy_order_counter               = orderbook_origination.storage.buyOrderCounter
    sell_order_counter              = orderbook_origination.storage.sellOrderCounter
    fee_ledger                      = orderbook_origination.storage.feeLedger
    currency_ledger                 = orderbook_origination.storage.currencyLedger
    rwa_order_ledger                = orderbook_origination.storage.rwaOrderLedger
    buy_order_ledger                = orderbook_origination.storage.buyOrderLedger
    sell_order_ledger               = orderbook_origination.storage.sellOrderLedger
    # pause_ledger                    = orderbook_origination.storage.pauseLedger

    # Get KYC
    kyc  = await models.Kyc.get(
        address = kyc_address
    )
    await kyc.save()

    # Prepare the orderbook
    orderbook = models.Orderbook(
        address                         = address,
        super_admin                     = super_admin,
        new_super_admin                 = new_super_admin,
        kyc                             = kyc,
        min_expiry_time                 = min_expiry_time,
        min_time_before_closing_order   = min_time_before_closing_order,
        min_buy_order_amount            = min_buy_order_amount,
        min_buy_order_value             = min_buy_order_value,
        min_sell_order_amount           = min_sell_order_amount,
        min_sell_order_value            = min_sell_order_value,
        buy_order_fee                   = buy_order_fee,
        sell_order_fee                  = sell_order_fee,
        place_buy_order_is_paused       = place_buy_order_is_paused,
        place_sell_order_is_paused      = place_sell_order_is_paused,
        cancel_orders_is_paused         = cancel_orders_is_paused,
        highest_buy_price_order_id      = highest_buy_price_order_id,
        highest_buy_price               = highest_buy_price,
        lowest_sell_price_order_id      = lowest_sell_price_order_id,
        lowest_sell_price               = lowest_sell_price,
        last_matched_price              = last_matched_price,
        last_matched_price_timestamp    = last_matched_price_timestamp,
        buy_order_counter               = buy_order_counter,
        sell_order_counter              = sell_order_counter
    )

    # Get RWA Token
    orderbook.rwa_token = await register_token(
        ctx = ctx,
        address = rwa_token_address
    )

    # Get contract metadata
    orderbook.metadata = await get_contract_metadata(
        ctx=ctx,
        address=address
    )

    # Save the orderbook
    await orderbook.save()

    # Prepare the fee ledger
    for currency_name in fee_ledger:
        fee_record      = fee_ledger[currency_name]
        fee_amount      = fee_record.nat_0
        paid_fee        = fee_record.nat_1
        currency, _     = await models.OrderbookCurrency.get_or_create(
            orderbook       = orderbook,
            currency_name   = currency_name
        )
        await currency.save()
        orderbook_fee   = models.OrderbookFee(
            orderbook   = orderbook,
            currency    = currency,
            fee_amount  = fee_amount,
            paid_fee    = paid_fee
        )
        await orderbook_fee.save()

    # Prepare the currency ledger
    for currency_record in currency_ledger:
        breakpoint()

    # Prepare the rwa order ledger
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record    = rwa_order_ledger[rwa_order_token_address]
        buy_price_map       = rwa_order_record.buyPriceMap
        sell_price_map      = rwa_order_record.sellPriceMap
        buy_order_map       = rwa_order_record.buyOrderMap
        sell_order_map      = rwa_order_record.sellOrderMap
        rwa_order_token     = await register_token(
            ctx = ctx,
            address = rwa_order_token_address
        )
        rwa_order           = models.OrderbookRwaOrder(
            orderbook   = orderbook,
            rwa_token   = rwa_order_token
        )
        await rwa_order.save()

        for buy_price in buy_price_map:
            breakpoint()

        for sell_price in sell_price_map:
            breakpoint()

        for buy_order in buy_order_map:
            breakpoint()

        for sell_order in sell_order_map:
            breakpoint()

    # Prepare the buy order ledger
    for buy_order_record in buy_order_ledger:
        breakpoint()

    # Prepare the sell order ledger
    for sell_order_record in sell_order_ledger:
        breakpoint()

    # # Save the entrypoints status
    # for entrypoint in pause_ledger:
    #     paused  = pause_ledger[entrypoint]
    #     entrypoint_status   = models.DodoMavEntrypointStatus(
    #         dodo_mav    = dodo_mav,
    #         entrypoint  = entrypoint,
    #         paused      = paused
    #     )
    #     await entrypoint_status.save()
