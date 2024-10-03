from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_guide_price import UpdateGuidePriceParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def update_guide_price(
    ctx: HandlerContext,
    update_guide_price: TezosTransaction[UpdateGuidePriceParameter, DodoMavStorage],
) -> None:
    breakpoint()