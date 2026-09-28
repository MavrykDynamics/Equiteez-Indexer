from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.execute_permit import ExecutePermitParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def execute_permit(
    ctx: HandlerContext,
    execute_permit: TezosTransaction[ExecutePermitParameter, KycStorage],
) -> None:
    # setMember / setMemberKyc / freezeMember run as the signer; the storage
    # effects are those of the direct entrypoints
    await sync_kyc_operation(ctx, execute_permit)
