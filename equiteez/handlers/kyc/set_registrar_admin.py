from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_registrar_admin import SetRegistrarAdminParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_registrar_admin(
    ctx: HandlerContext,
    set_registrar_admin: TezosTransaction[SetRegistrarAdminParameter, KycStorage],
) -> None:
    breakpoint()