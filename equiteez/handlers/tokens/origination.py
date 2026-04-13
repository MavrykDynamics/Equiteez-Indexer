import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination

from equiteez import models as models
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.utils.contract_allowlist import (
    BASE_TOKENS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.dynamic_index import attach_index_base_token
from equiteez.utils.utils import register_token

logger = logging.getLogger(__name__)


async def origination(
    ctx: HandlerContext,
    base_token_origination: TezosOrigination[BaseTokenStorage],
) -> None:
    address = base_token_origination.data.originated_contract_address
    first_level = base_token_origination.data.level

    if not address:
        return

    await attach_index_base_token(ctx, address, first_level=first_level)
    await register_token(ctx, address)

    allowlist = await fetch_allowlist()
    token = await models.Token.get_or_none(address=address, token_id=0)
    if token:
        token.in_allowlist = allowlist_contains(allowlist, BASE_TOKENS, address)
        await token.save()

    logger.info("Token %s registered at level %d", address, first_level)
