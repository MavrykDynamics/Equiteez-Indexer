from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, OrderbookStorage],
) -> None:
    # # Fetch operations info
    # address         = toggle_pause_entrypoint.data.target_address
    # pause_ledger    = toggle_pause_entrypoint.storage.pauseLedger

    # # Get orderbook
    # orderbook       = await models.Orderbook.get(
    #     address = address
    # )
    
    # # Save the entrypoints status
    # for entrypoint in pause_ledger:
    #     paused                      = pause_ledger[entrypoint]
    #     entrypoint_status, _        = await models.OrderbookEntrypointStatus.get_or_create(
    #         orderbook   = orderbook,
    #         entrypoint  = entrypoint
    #     )
    #     entrypoint_status.paused    = paused
    #     await entrypoint_status.save()
    ...