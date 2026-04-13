import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination

from equiteez import models
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.contract_allowlist import (
    SUPER_ADMINS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.dynamic_index import attach_index_super_admin
from equiteez.utils.utils import get_contract_metadata

logger = logging.getLogger(__name__)


async def origination(
    ctx: HandlerContext,
    super_admin_origination: TezosOrigination[SuperAdminStorage],
) -> None:
    address = super_admin_origination.data.originated_contract_address
    first_level = super_admin_origination.data.level

    if not address:
        return

    await attach_index_super_admin(ctx, address, first_level=first_level)

    signatory_ledger = super_admin_origination.storage.signatoryLedger
    signatory_size = super_admin_origination.storage.signatorySize
    action_counter = super_admin_origination.storage.actionCounter
    general_admin_ledger = super_admin_origination.storage.generalAdminLedger
    contract_admin_ledger = super_admin_origination.storage.contractAdminLedger
    threshold = super_admin_origination.storage.config.threshold
    action_expiry_in_seconds = (
        super_admin_origination.storage.config.actionExpiryInSeconds
    )

    allowlist = await fetch_allowlist()
    super_admin = models.SuperAdmin(
        address=address,
        signatory_size=signatory_size,
        action_counter=action_counter,
        threshold=threshold,
        action_expiry_in_seconds=action_expiry_in_seconds,
        in_allowlist=allowlist_contains(allowlist, SUPER_ADMINS, address),
    )
    super_admin.metadata = await get_contract_metadata(ctx=ctx, address=address)
    await super_admin.save()

    for signatory_address in signatory_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=signatory_address)
        await user.save()
        signatory = models.SuperAdminSignatory(super_admin=super_admin, user=user)
        await signatory.save()

    for general_admin_address in general_admin_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=general_admin_address)
        await user.save()
        general_admin, _ = await models.SuperAdminGeneralAdmin.get_or_create(
            super_admin=super_admin, user=user
        )
        await general_admin.save()

    for contract_admin_record in contract_admin_ledger:
        contract_admin_address = contract_admin_record.key.address_0
        contract_address = contract_admin_record.key.address_1
        user, _ = await models.EquiteezUser.get_or_create(
            address=contract_admin_address
        )
        await user.save()
        contract_admin, _ = await models.SuperAdminContractAdmin.get_or_create(
            super_admin=super_admin, user=user, contract_address=contract_address
        )
        await contract_admin.save()

    logger.info("super_admin %s registered at level %d", address, first_level)
