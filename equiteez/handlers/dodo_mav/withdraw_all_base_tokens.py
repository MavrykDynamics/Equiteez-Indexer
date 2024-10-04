from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_all_base_tokens import WithdrawAllBaseTokensParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_all_base_tokens(
    ctx: HandlerContext,
    withdraw_all_base_tokens: TezosTransaction[WithdrawAllBaseTokensParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = withdraw_all_base_tokens.data.target_address
    base_balance                = withdraw_all_base_tokens.storage.baseBalance
    target_base_token_amount    = withdraw_all_base_tokens.storage.targetBaseTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get(
        address = address
    )
    dodo_mav.base_balance               = base_balance
    dodo_mav.target_base_token_amount   = target_base_token_amount
    await dodo_mav.save()
