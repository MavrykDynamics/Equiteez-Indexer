from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.deposit_base_token import DepositBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def deposit_base_token(
    ctx: HandlerContext,
    deposit_base_token: TezosTransaction[DepositBaseTokenParameter, DodoMavStorage],
) -> None:
    ...