from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_member_kyc import SetMemberKycParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_member_kyc(
    ctx: HandlerContext,
    set_member_kyc: TezosTransaction[SetMemberKycParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_member_kyc)
