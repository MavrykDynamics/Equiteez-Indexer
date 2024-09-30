from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage
from equiteez.utils.utils import get_contract_metadata, register_token


async def origination(
    ctx: HandlerContext,
    dodo_mav_origination: TezosOrigination[DodoMavStorage],
) -> None:
    # Fetch operation info
    address                         = dodo_mav_origination.data.originated_contract_address
    super_admin                     = dodo_mav_origination.storage.superAdmin
    new_super_admin                 = dodo_mav_origination.storage.newSuperAdmin
    rwa_orderbook_address           = dodo_mav_origination.storage.rwaOrderbookAddress
    maintainer_fee                  = dodo_mav_origination.storage.config.maintainerFee
    lp_fee                          = dodo_mav_origination.storage.config.lpFee
    fee_decimals                    = dodo_mav_origination.storage.config.feeDecimals
    price_model                     = models.PriceModel.FIXED if dodo_mav_origination.storage.guidePriceConfig.priceModel == "fixed" else models.PriceModel.DYNAMIC
    appraisal_price                 = dodo_mav_origination.storage.guidePriceConfig.appraisalPrice
    fixed_price_percent             = dodo_mav_origination.storage.guidePriceConfig.fixedPricePercent
    orderbook_price_percent         = dodo_mav_origination.storage.guidePriceConfig.orderbookPricePercent
    quote_token_address             = dodo_mav_origination.storage.quoteToken.tokenContractAddress
    base_token_address              = dodo_mav_origination.storage.baseToken.tokenContractAddress
    quote_lp_token_address          = dodo_mav_origination.storage.quoteLpToken.tokenContractAddress
    base_lp_token_address           = dodo_mav_origination.storage.baseLpToken.tokenContractAddress
    quote_balance                   = dodo_mav_origination.storage.config.maintainerFee
    base_balance                    = dodo_mav_origination.storage.quoteBalance
    target_quote_token_amount       = dodo_mav_origination.storage.targetBaseTokenAmount
    target_base_token_amount        = dodo_mav_origination.storage.targetBaseTokenAmount
    quote_balance_limit             = dodo_mav_origination.storage.quoteBalanceLimit
    base_balance_limit              = dodo_mav_origination.storage.baseBalanceLimit
    r_status                        = dodo_mav_origination.storage.rStatus
    guide_price                     = dodo_mav_origination.storage.guidePrice
    slippage_factor                 = dodo_mav_origination.storage.slippageFactor

    # Get the orderbook
    orderbook   = models.Orderbook.get(
        address  = rwa_orderbook_address
    )

    # Register the various tokens
    quote_token = await register_token(
        ctx=ctx,
        address=quote_token_address
    )
    base_token = await register_token(
        ctx=ctx,
        address=base_token_address
    )
    quote_lp_token = await register_token(
        ctx=ctx,
        address=quote_lp_token_address
    )
    base_lp_token = await register_token(
        ctx=ctx,
        address=base_lp_token_address
    )

    # Prepare the dodo mav
    dodo_mav = models.DodoMav(
        address                         = address,
        super_admin                     = super_admin,
        new_super_admin                 = new_super_admin,
        orderbook                       = orderbook,
        maintainer_fee                  = maintainer_fee,
        lp_fee                          = lp_fee,
        fee_decimals                    = fee_decimals,
        price_model                     = price_model,
        appraisal_price                 = appraisal_price,
        fixed_price_percent             = fixed_price_percent,
        orderbook_price_percent         = orderbook_price_percent,
        quote_token                     = quote_token,
        base_token                      = base_token,
        quote_lp_token                  = quote_lp_token,
        base_lp_token                   = base_lp_token,
        quote_balance                   = quote_balance,
        base_balance                    = base_balance,
        target_quote_token_amount       = target_quote_token_amount,
        target_base_token_amount        = target_base_token_amount,
        quote_balance_limit             = quote_balance_limit,
        base_balance_limit              = base_balance_limit,
        r_status                        = r_status,
        guide_price                     = guide_price,
        slippage_factor                 = slippage_factor,
    )

    # Get contract metadata
    dodo_mav.metadata = await get_contract_metadata(
        ctx=ctx,
        address=address
    )

    breakpoint()

    # Save the orderbook
    await dodo_mav.save()
