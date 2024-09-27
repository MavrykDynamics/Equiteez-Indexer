from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.deposit_quote_token import DepositQuoteTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def deposit_quote_token(
    ctx: HandlerContext,
    deposit_quote_token: TezosTransaction[DepositQuoteTokenParameter, DodoMavStorage],
) -> None:
    ...