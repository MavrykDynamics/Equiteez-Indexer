from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.pause_all import PauseAllParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def pause_all(
    ctx: HandlerContext,
    pause_all: TezosTransaction[PauseAllParameter, KycStorage],
) -> None:
    # Fetch operation info
    address                     = pause_all.data.target_address
    set_member_is_paused        = pause_all.storage.breakGlassConfig.setMemberIsPaused
    freeze_member_is_paused     = pause_all.storage.breakGlassConfig.freezeMemberIsPaused
    unfreeze_member_is_paused   = pause_all.storage.breakGlassConfig.unfreezeMemberIsPaused

    # Get kyc
    kyc                         = await models.Kyc.get(
        address = address
    )

    # Update record
    kyc.set_member_is_paused        = set_member_is_paused
    kyc.freeze_member_is_paused     = freeze_member_is_paused
    kyc.unfreeze_member_is_paused   = unfreeze_member_is_paused
    await kyc.save()
