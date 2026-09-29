from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_valid_input import SetValidInputParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_valid_input(
    ctx: HandlerContext,
    set_valid_input: TezosTransaction[SetValidInputParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_valid_input)
