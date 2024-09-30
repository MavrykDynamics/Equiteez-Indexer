from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_all_quote_tokens import WithdrawAllQuoteTokensParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_all_quote_tokens(
    ctx: HandlerContext,
    withdraw_all_quote_tokens: TezosTransaction[WithdrawAllQuoteTokensParameter, DodoMavStorage],
) -> None:
    breakpoint()