from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.toggle_pause_entrypoint import (
    TogglePauseEntrypointParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[
        TogglePauseEntrypointParameter, KycStorage
    ],
) -> None:
    # Fetch operation info
    address = toggle_pause_entrypoint.data.target_address
    pause_ledger = toggle_pause_entrypoint.storage.pauseLedger

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Save the entrypoints status
    for entrypoint in pause_ledger:
        paused = pause_ledger[entrypoint]
        entrypoint_status, _ = await models.KycEntrypointStatus.get_or_create(
            contract=kyc, entrypoint=entrypoint
        )
        entrypoint_status.paused = paused
        await entrypoint_status.save()
