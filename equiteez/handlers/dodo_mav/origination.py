from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def origination(
    ctx: HandlerContext,
    dodo_mav_origination: TezosOrigination[DodoMavStorage],
) -> None:
    ...