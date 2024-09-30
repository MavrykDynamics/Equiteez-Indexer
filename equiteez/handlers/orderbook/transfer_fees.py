from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.transfer_fees import TransferFeesParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def transfer_fees(
    ctx: HandlerContext,
    transfer_fees: TezosTransaction[TransferFeesParameter, OrderbookStorage],
) -> None:
    breakpoint()