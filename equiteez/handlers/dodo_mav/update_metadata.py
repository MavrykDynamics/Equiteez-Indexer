from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage
from equiteez.utils.utils import get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, DodoMavStorage],
) -> None:
    # Fetch operations info
    address = update_metadata.data.target_address

    # Get dodo mav
    dodo_mav    = await models.DodoMav.get(
        address = address
    )

    # Update record
    dodo_mav.metadata = await get_contract_metadata(
        ctx=ctx,
        address=address
    )
