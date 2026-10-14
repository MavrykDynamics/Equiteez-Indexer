from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.freeze_member import FreezeMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def freeze_member(
    ctx: HandlerContext,
    freeze_member: TezosTransaction[FreezeMemberParameter, KycStorage],
) -> None:
    # One entrypoint freezes and unfreezes (freeze flag); unfreezeMember is gone
    await sync_kyc_operation(ctx, freeze_member)
