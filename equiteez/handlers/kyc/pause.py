from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.pause import PauseParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def pause(
    ctx: HandlerContext,
    pause: TezosTransaction[PauseParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, pause)
