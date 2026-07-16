from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_currency import SetCurrencyParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import register_token


async def set_currency(
    ctx: HandlerContext,
    set_currency: TezosTransaction[SetCurrencyParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = set_currency.data.target_address
    action_type = set_currency.parameter.actionType
    currency_name = set_currency.parameter.name
    currency_ledger = set_currency.storage.currencyLedger

    # On "remove" the currency is deleted from the currency ledger, so its key
    # is absent from the storage diff; keep the row (orders/fees reference it)
    if action_type == "remove" or currency_name not in currency_ledger:
        return

    # Update currencies
    currency_record = currency_ledger[currency_name]
    token_address = currency_record.tokenContractAddress
    orderbook = await models.Orderbook.get(address=address)
    token = await register_token(ctx=ctx, address=token_address)
    currency, _ = await models.OrderbookCurrency.get_or_create(
        orderbook=orderbook, currency_name=currency_name
    )
    currency.token = token
    await currency.save()
