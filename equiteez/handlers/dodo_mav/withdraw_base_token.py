from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.withdraw_base_token import WithdrawBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def withdraw_base_token(
    ctx: HandlerContext,
    withdraw_base_token: TezosTransaction[WithdrawBaseTokenParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address                     = withdraw_base_token.data.target_address
    base_balance                = withdraw_base_token.storage.baseBalance
    target_base_token_amount    = withdraw_base_token.storage.targetBaseTokenAmount

    # Get dodo mav
    dodo_mav        = await models.DodoMav.get_or_none(
        address = address
    )
    if not dodo_mav:
        return
    dodo_mav.base_balance               = base_balance
    dodo_mav.target_base_token_amount   = target_base_token_amount
    await dodo_mav.save()
