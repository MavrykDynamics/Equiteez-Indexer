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
    # save() rather than a bulk update(): the DualCursor consumers page by
    # updated_at, and only save() runs the auto_now bump
    for token in await models.Token.filter(address=kill.data.target_address):
        token.is_killed = kill.storage.isKilled
        await token.save()
