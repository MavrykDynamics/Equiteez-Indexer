from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_base_token import WithdrawBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_base_token(
    ctx: HandlerContext,
    withdraw_base_token: TezosTransaction[WithdrawBaseTokenParameter, DodoMavStorage],
) -> None:
    breakpoint()