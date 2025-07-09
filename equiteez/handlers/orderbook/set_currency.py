from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_currency import SetCurrencyParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def set_currency(
    ctx: HandlerContext,
    set_currency: TezosTransaction[SetCurrencyParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = set_currency.data.target_address
    currency_name = set_currency.parameter.name
    currency_ledger = set_currency.storage.currencyLedger

    # Update currencies
    currency_record = currency_ledger[currency_name]
    token_address = currency_record.tokenContractAddress
    orderbook = await models.Orderbook.get(address=address)
    token, _ = await models.Token.get_or_create(address=token_address)
    await token.save()
    currency, _ = await models.OrderbookCurrency.get_or_create(
        orderbook=orderbook, currency_name=currency_name
    )
    currency.token = token
    await currency.save()
