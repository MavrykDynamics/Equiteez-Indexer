from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_blacklist import SetBlacklistParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_blacklist(
    ctx: HandlerContext,
    set_blacklist: TezosTransaction[SetBlacklistParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_blacklist)
