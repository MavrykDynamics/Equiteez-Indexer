from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.base_token.tezos_parameters.transfer import TransferParameter as BaseTokenTransferParameter
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.types.dodo_mav.tezos_parameters.sell_base_token import SellBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage
from equiteez.types.quote_token.tezos_parameters.transfer import TransferParameter as MaintainerFeeParameter
from equiteez.types.quote_token.tezos_parameters.transfer import TransferParameter as QuoteTokenTransferParameter
from equiteez.types.quote_token.tezos_storage import QuoteTokenStorage
from dateutil import parser

async def sell_base_token(
    ctx: HandlerContext,
    sell_base_token: TezosTransaction[SellBaseTokenParameter, DodoMavStorage],
    quote_token_transfer: TezosTransaction[QuoteTokenTransferParameter, QuoteTokenStorage],
    base_token_transfer: TezosTransaction[BaseTokenTransferParameter, BaseTokenStorage],
    maintainer_fee: TezosTransaction[MaintainerFeeParameter, QuoteTokenStorage] | None,
) -> None:
    # Fetch operation info
    address                     = sell_base_token.data.target_address
    trader_address              = sell_base_token.data.sender_address
    timestamp                   = parser.parse(sell_base_token.data.timestamp)
    quote_token_qty             = quote_token_transfer.parameter.root[0].txs[0].amount
    base_token_qty              = base_token_transfer.parameter.root[0].txs[0].amount
    level                       = sell_base_token.data.level
    quote_balance               = sell_base_token.storage.quoteBalance
    base_balance                = sell_base_token.storage.baseBalance
    r_status                    = sell_base_token.storage.rStatus
    target_base_token_amount    = sell_base_token.storage.targetBaseTokenAmount
    target_quote_token_amount   = sell_base_token.storage.targetQuoteTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get_or_none(
        address = address
    )
    if not dodo_mav:
        return
    dodo_mav.quote_balance              = quote_balance
    dodo_mav.base_balance               = base_balance
    dodo_mav.target_base_token_amount   = target_base_token_amount
    dodo_mav.target_quote_token_amount  = target_quote_token_amount
    dodo_mav.r_status                   = r_status
    await dodo_mav.save()

    # querysellbasetoken => give the price of the base token (huge views so very complex to integrate): sellBaseToken
    # Let frontend call the view and do the calculation

    # Save history data
    trader, _                   = await models.EquiteezUser.get_or_create(
        address = trader_address
    )
    await trader.save()
    if float(base_token_qty) > 0 and float(quote_token_qty) > 0:
        base_token_price            = float(quote_token_qty) / float(base_token_qty)
        history_data                = models.DodoMavHistoryData(
            dodo_mav            = dodo_mav,
            trader              = trader,
            timestamp           = timestamp,
            level               = level,
            type                = models.TradeType.SELL,
            base_token_price    = base_token_price,
            base_token_qty      = base_token_qty,
            quote_token_qty     = quote_token_qty,
            base_token_pool     = base_balance,
            quote_token_pool    = quote_balance
        )
        await history_data.save()
