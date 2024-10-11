from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, SuperAdminStorage],
) -> None:
    # Fetch operations info
    address = update_metadata.data.target_address

    # Get super admin
    super_admin = await models.SuperAdmin.get(
        address = address
    )

    # Update record
    super_admin.metadata    = await get_contract_metadata(
        ctx=ctx,
        address=address
    )
