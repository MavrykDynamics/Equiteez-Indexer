from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_baker import SetBakerParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_baker(
    ctx: HandlerContext,
    set_baker: TezosTransaction[SetBakerParameter, SuperAdminStorage],
) -> None:
    # Fetch operations info
    address = set_baker.data.target_address
    baker = set_baker.storage.baker

    # Record signatory action
    await create_super_admin_action(set_baker)

    # Update baker
    super_admin = await models.SuperAdmin.get(address=address)
    super_admin.baker = baker
    await super_admin.save()
