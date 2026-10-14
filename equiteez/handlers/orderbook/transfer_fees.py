from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.transfer_fees import (
    TransferFeesParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import sync_fee_ledger


async def transfer_fees(
    ctx: HandlerContext,
    transfer_fees: TezosTransaction[TransferFeesParameter, OrderbookStorage],
) -> None:
    orderbook = await models.Orderbook.get(address=transfer_fees.data.target_address)
    await sync_fee_ledger(orderbook, transfer_fees.storage)
