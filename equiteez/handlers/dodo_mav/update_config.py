from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_config import UpdateConfigParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, DodoMavStorage],
) -> None:
    breakpoint()