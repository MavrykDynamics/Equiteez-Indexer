import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination

from equiteez import models
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
    token_origination: TezosOrigination[BaseTokenStorage],
) -> None:
    address = token_origination.data.originated_contract_address
    first_level = token_origination.data.level

    if not address:
        return

    tracked, _ = await models.TrackedContract.get_or_create(
        address=address,
        defaults={
            "contract_type": models.ContractType.BASE_TOKEN,
            "first_level": first_level,
            "status": models.ContractStatus.PENDING,
        },
    )

    if tracked.status == models.ContractStatus.INDEXED:
        return

    allowlist = await fetch_allowlist()
    if not allowlist_contains(allowlist, BASE_TOKENS, address):
        logger.info("base_token %s not in allowlist, saved as PENDING at level %d", address, first_level)
        return

    await attach_index_base_token(ctx, address, first_level=tracked.first_level)
    await register_token(ctx, address)
    logger.info("Token %s registered at level %d", address, first_level)
