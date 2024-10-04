from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.deposit_quote_token import DepositQuoteTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def deposit_quote_token(
    ctx: HandlerContext,
    deposit_quote_token: TezosTransaction[DepositQuoteTokenParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = deposit_quote_token.data.target_address
    quote_balance               = deposit_quote_token.storage.quoteBalance
    target_quote_token_amount   = deposit_quote_token.storage.targetQuoteTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get(
        address = address
    )
    dodo_mav.quote_balance              = quote_balance
    dodo_mav.target_quote_token_amount  = target_quote_token_amount
    await dodo_mav.save()
