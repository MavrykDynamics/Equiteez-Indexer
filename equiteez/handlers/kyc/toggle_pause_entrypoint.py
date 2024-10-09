from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, KycStorage],
) -> None:
    # Fetch operation info
    address                     = toggle_pause_entrypoint.data.target_address
    set_member_is_paused        = toggle_pause_entrypoint.storage.breakGlassConfig.setMemberIsPaused
    freeze_member_is_paused     = toggle_pause_entrypoint.storage.breakGlassConfig.freezeMemberIsPaused
    unfreeze_member_is_paused   = toggle_pause_entrypoint.storage.breakGlassConfig.unfreezeMemberIsPaused

    # Get kyc
    kyc                         = await models.Kyc.get(
        address = address
    )

    # Update record
    kyc.set_member_is_paused        = set_member_is_paused
    kyc.freeze_member_is_paused     = freeze_member_is_paused
    kyc.unfreeze_member_is_paused   = unfreeze_member_is_paused
    await kyc.save()
