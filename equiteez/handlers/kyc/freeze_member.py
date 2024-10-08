from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.freeze_member import FreezeMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def freeze_member(
    ctx: HandlerContext,
    freeze_member: TezosTransaction[FreezeMemberParameter, KycStorage],
) -> None:
    breakpoint()