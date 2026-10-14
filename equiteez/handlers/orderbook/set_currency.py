from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_currency import SetCurrencyParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import sync_currencies


async def set_currency(
    ctx: HandlerContext,
    set_currency: TezosTransaction[SetCurrencyParameter, OrderbookStorage],
) -> None:
    # On "remove" the key disappears from the currency ledger and is absent
    # from the storage diff; keep the row (orders/fees reference it)
    orderbook = await models.Orderbook.get(address=set_currency.data.target_address)
    await sync_currencies(ctx, orderbook, set_currency.storage)
