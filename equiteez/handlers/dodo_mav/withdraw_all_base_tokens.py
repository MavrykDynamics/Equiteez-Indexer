from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_all_base_tokens import WithdrawAllBaseTokensParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_all_base_tokens(
    ctx: HandlerContext,
    withdraw_all_base_tokens: TezosTransaction[WithdrawAllBaseTokensParameter, DodoMavStorage],
) -> None:
    ...