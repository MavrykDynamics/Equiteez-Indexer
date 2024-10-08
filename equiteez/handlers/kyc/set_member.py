from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_member import SetMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_member(
    ctx: HandlerContext,
    set_member: TezosTransaction[SetMemberParameter, KycStorage],
) -> None:
    breakpoint()