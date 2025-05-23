from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTokenBalanceData
from equiteez import models as models

async def on_balance_update(
    ctx: HandlerContext,
    token_balance: TezosTokenBalanceData,
) -> None:
    # Fetch operation info
    address         = token_balance.contract_address
    account_address = token_balance.account_address
    balance         = token_balance.balance

    # Register token
    token           = await models.Token.get_or_none(
        address = address
    )
    if not token:
        return

    # Update user balance
    user, _         = await models.EquiteezUser.get_or_create(
        address = account_address
    )
    await user.save()
    user_balance, _ = await models.EquiteezUserBalance.get_or_create(
        user    = user,
        token   = token
    )
    user_balance.balance    = balance
    await user_balance.save()
