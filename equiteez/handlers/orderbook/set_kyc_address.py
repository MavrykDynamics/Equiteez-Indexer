from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_kyc_address import SetKycAddressParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def set_kyc_address(
    ctx: HandlerContext,
    set_kyc_address: TezosTransaction[SetKycAddressParameter, OrderbookStorage],
) -> None:
    breakpoint()