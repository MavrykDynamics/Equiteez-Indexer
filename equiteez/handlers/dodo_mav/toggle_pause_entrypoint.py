from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, DodoMavStorage],
) -> None:
    # Fetch operations info
    address         = toggle_pause_entrypoint.data.target_address
    pause_ledger    = toggle_pause_entrypoint.storage.pauseLedger

    # Get dodo mav
    dodo_mav    = await models.DodoMav.get(
        address = address
    )
    
    # Save the entrypoints status
    for entrypoint in pause_ledger:
        paused                      = pause_ledger[entrypoint]
        entrypoint_status, _        = await models.DodoMavEntrypointStatus.get_or_create(
            contract    = dodo_mav,
            entrypoint  = entrypoint
        )
        entrypoint_status.paused    = paused
        await entrypoint_status.save()
