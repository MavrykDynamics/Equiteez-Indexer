from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, DodoMavStorage],
) -> None:
    breakpoint()