from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_signatory import (
    SetSignatoryParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_signatory(
    ctx: HandlerContext,
    set_signatory: TezosTransaction[SetSignatoryParameter, SuperAdminStorage],
) -> None:
    # The add / remove semantics (parameter updateType) are captured in the
    # action type and data map; the signatory ledger itself is only updated
    # once the action is executed via signAction
    await create_super_admin_action(set_signatory)
