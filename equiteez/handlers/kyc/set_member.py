from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_member import SetMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_member(
    ctx: HandlerContext,
    set_member: TezosTransaction[SetMemberParameter, KycStorage],
) -> None:
    # The registrar is the caller, a delegated admin or a permit signer; the
    # memberLedger key carries it either way
    await sync_kyc_operation(ctx, set_member)
