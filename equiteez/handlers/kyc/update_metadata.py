from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.utils import get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, KycStorage],
) -> None:
    # Fetch operations info
    address = update_metadata.data.target_address

    # Get kyc
    kyc     = await models.Kyc.get(
        address = address
    )

    # Update record
    kyc.metadata = await get_contract_metadata(
        ctx=ctx,
        address=address
    )
