from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_all_quote_tokens import WithdrawAllQuoteTokensParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_all_quote_tokens(
    ctx: HandlerContext,
    withdraw_all_quote_tokens: TezosTransaction[WithdrawAllQuoteTokensParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = withdraw_all_quote_tokens.data.target_address
    quote_balance               = withdraw_all_quote_tokens.storage.quoteBalance
    target_quote_token_amount   = withdraw_all_quote_tokens.storage.targetQuoteTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get_or_none(
        address = address
    )
    if not dodo_mav:
        return
    dodo_mav.quote_balance              = quote_balance
    dodo_mav.target_quote_token_amount  = target_quote_token_amount
    await dodo_mav.save()
