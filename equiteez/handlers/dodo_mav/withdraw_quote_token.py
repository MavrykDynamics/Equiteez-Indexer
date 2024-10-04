from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_quote_token import WithdrawQuoteTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_quote_token(
    ctx: HandlerContext,
    withdraw_quote_token: TezosTransaction[WithdrawQuoteTokenParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = withdraw_quote_token.data.target_address
    quote_balance               = withdraw_quote_token.storage.quoteBalance
    target_quote_token_amount   = withdraw_quote_token.storage.targetQuoteTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get(
        address = address
    )
    dodo_mav.quote_balance              = quote_balance
    dodo_mav.target_quote_token_amount  = target_quote_token_amount
    await dodo_mav.save()
