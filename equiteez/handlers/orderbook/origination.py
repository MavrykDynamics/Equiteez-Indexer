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
    pause_ledger                    = orderbook_origination.storage.pauseLedger

    # Get KYC
    kyc, _      = await models.Kyc.get_or_create(
        address = kyc_address
    )
    await kyc.save()

    # Prepare the orderbook
    orderbook, _ = await models.Orderbook.get_or_create(
        address                         = address
    )
    orderbook.super_admin                     = super_admin
    orderbook.new_super_admin                 = new_super_admin
    orderbook.kyc                             = kyc
    orderbook.min_expiry_time                 = min_expiry_time
    orderbook.min_time_before_closing_order   = min_time_before_closing_order
    orderbook.min_buy_order_amount            = min_buy_order_amount
    orderbook.min_buy_order_value             = min_buy_order_value
    orderbook.min_sell_order_amount           = min_sell_order_amount
    orderbook.min_sell_order_value            = min_sell_order_value
    orderbook.buy_order_fee                   = buy_order_fee
    orderbook.sell_order_fee                  = sell_order_fee
    orderbook.highest_buy_price_order_id      = highest_buy_price_order_id
    orderbook.highest_buy_price               = highest_buy_price
    orderbook.lowest_sell_price_order_id      = lowest_sell_price_order_id
    orderbook.lowest_sell_price               = lowest_sell_price
    orderbook.last_matched_price              = last_matched_price
    orderbook.last_matched_price_timestamp    = last_matched_price_timestamp
    orderbook.buy_order_counter               = buy_order_counter
    orderbook.sell_order_counter              = sell_order_counter

    # Get RWA Token
    orderbook.rwa_token = await register_token(
        ctx     = ctx,
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
    for currency_name in currency_ledger:
        currency_record     = currency_ledger[currency_name]
        token_address       = currency_record.tokenContractAddress
        token               = await register_token(
            ctx     = ctx,
            address = token_address
        )
        currency, _         = await models.OrderbookCurrency.get_or_create(
            orderbook       = orderbook,
            currency_name   = currency_name
        )
        currency.token      = token
        await currency.save()

    # Save the entrypoints status
    for entrypoint in pause_ledger:
        paused  = pause_ledger[entrypoint]
        entrypoint_status   = models.OrderbookEntrypointStatus(
            contract    = orderbook,
            entrypoint  = entrypoint,
            paused      = paused
        )
        await entrypoint_status.save()
