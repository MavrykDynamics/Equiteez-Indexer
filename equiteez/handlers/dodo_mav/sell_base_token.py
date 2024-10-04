from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.sell_base_token import SellBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def sell_base_token(
    ctx: HandlerContext,
    sell_base_token: TezosTransaction[SellBaseTokenParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = sell_base_token.data.target_address
    quote_balance               = sell_base_token.storage.quoteBalance
    base_balance                = sell_base_token.storage.baseBalance
    r_status                    = sell_base_token.storage.rStatus
    target_base_token_amount    = sell_base_token.storage.targetBaseTokenAmount
    target_quote_token_amount   = sell_base_token.storage.targetQuoteTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get(
        address = address
    )
    dodo_mav.quote_balance              = quote_balance
    dodo_mav.base_balance               = base_balance
    dodo_mav.target_base_token_amount   = target_base_token_amount
    dodo_mav.target_quote_token_amount  = target_quote_token_amount
    dodo_mav.r_status                   = r_status
    await dodo_mav.save()

    # querysellbasetoken => give the price of the base token (huge views so very complex to integrate): sellBaseToken
    # Let frontend call the view and do the calculation
