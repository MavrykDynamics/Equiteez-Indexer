from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, DodoMavStorage],
) -> None:
    breakpoint()