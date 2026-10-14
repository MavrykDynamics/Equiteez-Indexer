from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.permit_and_execute import (
    PermitAndExecuteParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def permit_and_execute(
    ctx: HandlerContext,
    permit_and_execute: TezosTransaction[PermitAndExecuteParameter, KycStorage],
) -> None:
    # setMember / setMemberKyc / freezeMember run as the signer; the storage
    # effects are those of the direct entrypoints
    await sync_kyc_operation(ctx, permit_and_execute)
