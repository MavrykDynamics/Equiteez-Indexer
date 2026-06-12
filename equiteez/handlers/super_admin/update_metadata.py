from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.update_metadata import (
    UpdateMetadataParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action, get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, SuperAdminStorage],
) -> None:
    # Fetch operations info
    address = update_metadata.data.target_address

    # Record signatory action
    await create_super_admin_action(update_metadata)

    # Get super admin
    super_admin = await models.SuperAdmin.get(address=address)

    # Update record
    super_admin.metadata = await get_contract_metadata(ctx=ctx, address=address)
    await super_admin.save()
