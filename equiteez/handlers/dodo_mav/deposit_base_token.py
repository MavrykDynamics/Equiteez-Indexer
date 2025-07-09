from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.deposit_base_token import (
    DepositBaseTokenParameter,
)
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def deposit_base_token(
    ctx: HandlerContext,
    deposit_base_token: TezosTransaction[DepositBaseTokenParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address = deposit_base_token.data.target_address
    base_balance = deposit_base_token.storage.baseBalance
    target_base_token_amount = deposit_base_token.storage.targetBaseTokenAmount

    # Get dodo mav
    dodo_mav = await models.DodoMav.get_or_none(address=address)
    if not dodo_mav:
        return
    dodo_mav.base_balance = base_balance
    dodo_mav.target_base_token_amount = target_base_token_amount
    await dodo_mav.save()
