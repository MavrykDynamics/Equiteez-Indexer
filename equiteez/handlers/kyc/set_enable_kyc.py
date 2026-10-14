from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_enable_kyc import SetEnableKycParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_enable_kyc(
    ctx: HandlerContext,
    set_enable_kyc: TezosTransaction[SetEnableKycParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_enable_kyc)
