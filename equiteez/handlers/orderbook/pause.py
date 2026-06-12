from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.pause import PauseParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def pause(
    ctx: HandlerContext,
    pause: TezosTransaction[PauseParameter, OrderbookStorage],
) -> None:
    # Fetch operations info
    address = pause.data.target_address
    pause_ledger = pause.storage.pauseLedger

    # Get orderbook
    orderbook = await models.Orderbook.get(address=address)

    # Save the entrypoints status
    for entrypoint in pause_ledger:
        paused = pause_ledger[entrypoint]
        entrypoint_status, _ = await models.OrderbookEntrypointStatus.get_or_create(
            contract=orderbook, entrypoint=entrypoint
        )
        entrypoint_status.paused = paused
        await entrypoint_status.save()
