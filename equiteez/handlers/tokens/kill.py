from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.base_token.tezos_parameters.kill import KillParameter
from equiteez.types.base_token.tezos_storage import BaseTokenStorage


async def kill(
    ctx: HandlerContext,
    kill: TezosTransaction[KillParameter, BaseTokenStorage],
) -> None:
    # Terminal: the contract clears ledger, supply and operators and rejects
    # every later call. Normally reached through the super admin's killToken
    # action, i.e. as an internal operation
    await models.Token.filter(address=kill.data.target_address).update(
        is_killed=kill.storage.isKilled
    )
