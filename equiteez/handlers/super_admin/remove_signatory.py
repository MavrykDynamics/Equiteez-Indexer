from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.remove_signatory import (
    RemoveSignatoryParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def remove_signatory(
    ctx: HandlerContext,
    remove_signatory: TezosTransaction[RemoveSignatoryParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(remove_signatory)
