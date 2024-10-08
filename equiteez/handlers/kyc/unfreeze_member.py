from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.unfreeze_member import UnfreezeMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def unfreeze_member(
    ctx: HandlerContext,
    unfreeze_member: TezosTransaction[UnfreezeMemberParameter, KycStorage],
) -> None:
    breakpoint()