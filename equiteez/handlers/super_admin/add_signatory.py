from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.add_signatory import (
    AddSignatoryParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def add_signatory(
    ctx: HandlerContext,
    add_signatory: TezosTransaction[AddSignatoryParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(add_signatory)
