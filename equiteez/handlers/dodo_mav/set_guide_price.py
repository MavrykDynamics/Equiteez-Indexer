from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.set_guide_price import SetGuidePriceParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def set_guide_price(
    ctx: HandlerContext,
    set_guide_price: TezosTransaction[SetGuidePriceParameter, DodoMavStorage],
) -> None:
    breakpoint()