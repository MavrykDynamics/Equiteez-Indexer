import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination

from equiteez import models as models
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.contract_allowlist import (
    LAUNCHPADS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.launchpad_utils import (
    upsert_launch_from_record,
    upsert_sale_option,
)
from equiteez.utils.utils import get_contract_metadata

logger = logging.getLogger(__name__)


async def origination(
    ctx: HandlerContext,
    launchpad_origination: TezosOrigination[LaunchpadStorage],
) -> None:
    address = launchpad_origination.data.originated_contract_address
    if not address:
        return

    first_level = launchpad_origination.data.level
    storage = launchpad_origination.storage

    kyc, _ = await models.Kyc.get_or_create(address=storage.membershipKycAddress)
    await kyc.save()

    allowlist = await fetch_allowlist()
    metadata = await get_contract_metadata(ctx=ctx, address=address)
    defaults = {
        "super_admin": storage.superAdmin,
        "new_super_admin": storage.newSuperAdmin,
        "membership_kyc": kyc,
        "metadata": metadata,
        "in_allowlist": allowlist_contains(allowlist, LAUNCHPADS, address),
    }
    launchpad, created = await models.Launchpad.get_or_create(
        address=address, defaults=defaults
    )
    if not created:
        for k, v in defaults.items():
            setattr(launchpad, k, v)
        await launchpad.save()

    for name, treasury_address in storage.treasuryLedger.items():
        treasury, _ = await models.LaunchpadTreasury.get_or_create(
            launchpad=launchpad,
            name=name,
            defaults={"address": treasury_address},
        )
        if treasury.address != treasury_address:
            treasury.address = treasury_address
            await treasury.save()

    for entrypoint, paused in storage.pauseLedger.items():
        status, _ = await models.LaunchpadEntrypointStatus.get_or_create(
            contract=launchpad, entrypoint=entrypoint
        )
        status.paused = paused
        await status.save()

    for launch_name, launch_record in storage.launchLedger.items():
        launch = await upsert_launch_from_record(
            ctx, launchpad, launch_name, launch_record
        )
        for option_name, option_record in launch_record.saleOptions.items():
            await upsert_sale_option(ctx, launch, option_name, option_record)

    for item in storage.purchaseLedger:
        launch_name = item.key.string
        user_address = item.key.address
        record = item.value

        launch = await models.LaunchpadLaunch.get_or_none(
            launchpad=launchpad, name=launch_name
        )
        if not launch:
            logger.warning(
                "Launchpad origination: purchaseLedger references unknown launch %s",
                launch_name,
            )
            continue

        user, _ = await models.EquiteezUser.get_or_create(address=user_address)
        await user.save()

        purchase, _ = await models.LaunchpadPurchase.get_or_create(
            launch=launch, user=user
        )
        purchase.total_purchased = int(record.totalPurchased)
        purchase.total_distributed = int(record.totalDistributed)
        await purchase.save()

        for option_name, amount_raw in record.purchased.items():
            sale_option = await models.LaunchpadSaleOption.get_or_none(
                launch=launch, name=option_name
            )
            if not sale_option:
                continue
            by_option, _ = await models.LaunchpadPurchaseByOption.get_or_create(
                purchase=purchase, sale_option=sale_option
            )
            by_option.amount = int(amount_raw)
            await by_option.save()

    logger.info("Launchpad %s registered at level %d", address, first_level)
