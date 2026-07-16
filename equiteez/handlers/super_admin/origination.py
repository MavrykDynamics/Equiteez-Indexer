from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.contract_allowlist import (
    SUPER_ADMINS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.utils import get_contract_metadata


async def origination(
    ctx: HandlerContext,
    super_admin_origination: TezosOrigination[SuperAdminStorage],
) -> None:
    # Fetch operation info
    address = super_admin_origination.data.originated_contract_address

    if not address:
        return

    signatory_ledger = super_admin_origination.storage.signatoryLedger
    signatory_size = super_admin_origination.storage.signatorySize
    action_counter = super_admin_origination.storage.actionCounter
    user_role_ledger = super_admin_origination.storage.userRoleLedger
    baker = super_admin_origination.storage.baker
    threshold = super_admin_origination.storage.config.threshold
    action_expiry_in_seconds = (
        super_admin_origination.storage.config.actionExpiryInSeconds
    )

    allowlist = await fetch_allowlist()

    # Prepare the super admin
    super_admin = models.SuperAdmin(
        address=address,
        signatory_size=signatory_size,
        action_counter=action_counter,
        threshold=threshold,
        action_expiry_in_seconds=action_expiry_in_seconds,
        baker=baker,
        in_allowlist=allowlist_contains(allowlist, SUPER_ADMINS, address),
    )

    # Get contract metadata
    super_admin.metadata = await get_contract_metadata(ctx=ctx, address=address)

    # Save the super admin
    await super_admin.save()

    # Save the signatories
    for signatory_address in signatory_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=signatory_address)
        await user.save()
        signatory = models.SuperAdminSignatory(super_admin=super_admin, user=user)
        await signatory.save()

    # Save the user roles
    for user_role_record in user_role_ledger:
        # Fetch params
        role_user_address = user_role_record.key.address_0
        role = user_role_record.key.string
        contract_address = user_role_record.key.address_1

        # Save user role
        user, _ = await models.EquiteezUser.get_or_create(address=role_user_address)
        await user.save()
        user_role, _ = await models.SuperAdminUserRole.get_or_create(
            super_admin=super_admin,
            user=user,
            role=role,
            contract_address=contract_address,
        )
        await user_role.save()
