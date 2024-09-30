from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_quote_token import WithdrawQuoteTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_quote_token(
    ctx: HandlerContext,
    withdraw_quote_token: TezosTransaction[WithdrawQuoteTokenParameter, DodoMavStorage],
) -> None:
    breakpoint()