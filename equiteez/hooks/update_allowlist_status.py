import logging

from dipdup.context import HookContext

from equiteez import models
from equiteez.utils.contract_allowlist import (
    BASE_TOKENS,
    KYC,
    LAUNCHPADS,
    ORDERBOOKS,
    SUPER_ADMINS,
    allowlist_contains,
    fetch_allowlist,
)

logger = logging.getLogger(__name__)


async def update_allowlist_status(
    ctx: HookContext,
) -> None:
    logger.info("update_allowlist_status: starting")

    allowlist = await fetch_allowlist()
    if allowlist is None:
        logger.warning("update_allowlist_status: allowlist fetch failed, skipping")
        return

    updated = 0

    for token in await models.Token.all():
        new_status = allowlist_contains(allowlist, BASE_TOKENS, token.address)
        if token.in_allowlist != new_status:
            token.in_allowlist = new_status
            await token.save()
            updated += 1

    for orderbook in await models.Orderbook.all():
        new_status = allowlist_contains(allowlist, ORDERBOOKS, orderbook.address)
        if orderbook.in_allowlist != new_status:
            orderbook.in_allowlist = new_status
            await orderbook.save()
            updated += 1

    for super_admin in await models.SuperAdmin.all():
        new_status = allowlist_contains(allowlist, SUPER_ADMINS, super_admin.address)
        if super_admin.in_allowlist != new_status:
            super_admin.in_allowlist = new_status
            await super_admin.save()
            updated += 1

    for kyc in await models.Kyc.all():
        new_status = allowlist_contains(allowlist, KYC, kyc.address)
        if kyc.in_allowlist != new_status:
            kyc.in_allowlist = new_status
            await kyc.save()
            updated += 1

    for launchpad in await models.Launchpad.all():
        new_status = allowlist_contains(allowlist, LAUNCHPADS, launchpad.address)
        if launchpad.in_allowlist != new_status:
            launchpad.in_allowlist = new_status
            await launchpad.save()
            updated += 1

    logger.info("update_allowlist_status: done, %d row(s) updated", updated)
