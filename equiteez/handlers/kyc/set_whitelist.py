from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_whitelist import SetWhitelistParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_whitelist(
    ctx: HandlerContext,
    set_whitelist: TezosTransaction[SetWhitelistParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_whitelist)
