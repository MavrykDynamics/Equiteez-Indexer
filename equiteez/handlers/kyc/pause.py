from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.pause import PauseParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def pause(
    ctx: HandlerContext,
    pause: TezosTransaction[PauseParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = pause.data.target_address

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Save the entrypoints status
    for item in pause.parameter.root:
        entrypoint_status, _ = await models.KycEntrypointStatus.get_or_create(
            contract=kyc, entrypoint=item.entrypoint
        )
        entrypoint_status.paused = item.pauseBool
        await entrypoint_status.save()
