import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.models.launchpad import PurchaseSource
from equiteez.types.launchpad.tezos_parameters.purchase import PurchaseParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import apply_purchase

logger = logging.getLogger(__name__)


async def purchase(
    ctx: HandlerContext,
    purchase: TezosTransaction[PurchaseParameter, LaunchpadStorage],
) -> None:
    address = purchase.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    launch_name = purchase.parameter.launchName
    sale_option_name = purchase.parameter.saleOption
    user_address = purchase.data.sender_address

    storage = purchase.storage

    launch_record = storage.launchLedger.get(launch_name)
    if launch_record is None:
        logger.warning("purchase: launch %s not in storage; skipping", launch_name)
        return

    sale_option_record = launch_record.saleOptions.get(sale_option_name)
    if sale_option_record is None:
        logger.warning(
            "purchase: sale option %s not in launch %s storage; skipping",
            sale_option_name,
            launch_name,
        )
        return

    purchase_record = None
    for item in storage.purchaseLedger:
        if item.key.string == launch_name and item.key.address == user_address:
            purchase_record = item.value
            break

    if purchase_record is None:
        logger.warning(
            "purchase: no ledger entry for (%s, %s); skipping",
            launch_name,
            user_address,
        )
        return

    await apply_purchase(
        ctx=ctx,
        launchpad=launchpad,
        launch_name=launch_name,
        user_address=user_address,
        sale_option_name=sale_option_name,
        payment_name=purchase.parameter.payment,
        event_amount=int(purchase.parameter.amount),
        operation_hash=purchase.data.hash,
        timestamp=purchase.data.timestamp,
        level=purchase.data.level,
        source=PurchaseSource.USER,
        launch_record=launch_record,
        sale_option_record=sale_option_record,
        purchase_record=purchase_record,
    )
