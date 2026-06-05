import logging

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.models.launchpad import PurchaseSource
from equiteez.types.launchpad.tezos_parameters.set_purchase_record import (
    SetPurchaseRecordParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import apply_purchase

logger = logging.getLogger(__name__)


async def set_purchase_record(
    ctx: HandlerContext,
    set_purchase_record: TezosTransaction[SetPurchaseRecordParameter, LaunchpadStorage],
) -> None:
    """Admin batch path. Each item applies via apply_purchase so totals and
    events stay consistent with the user-initiated `purchase` flow."""
    address = set_purchase_record.data.target_address
    launchpad = await models.Launchpad.get(address=address)
    storage = set_purchase_record.storage

    ledger_by_key = {
        (item.key.string, item.key.address): item.value
        for item in storage.purchaseLedger
    }

    for batch_index, item in enumerate(set_purchase_record.parameter.root):
        launch_record = storage.launchLedger.get(item.launchName)
        if launch_record is None:
            logger.warning(
                "setPurchaseRecord: launch %s not in storage; skipping item",
                item.launchName,
            )
            continue

        sale_option_record = launch_record.saleOptions.get(item.saleOption)
        if sale_option_record is None:
            logger.warning(
                "setPurchaseRecord: sale option %s not in launch %s; skipping item",
                item.saleOption,
                item.launchName,
            )
            continue

        purchase_record = ledger_by_key.get((item.launchName, item.purchaser))
        if purchase_record is None:
            logger.warning(
                "setPurchaseRecord: no ledger entry for (%s, %s); skipping item",
                item.launchName,
                item.purchaser,
            )
            continue

        await apply_purchase(
            ctx=ctx,
            launchpad=launchpad,
            launch_name=item.launchName,
            user_address=item.purchaser,
            sale_option_name=item.saleOption,
            payment_name=item.payment,
            event_amount=int(item.amount),
            operation_hash=set_purchase_record.data.hash,
            timestamp=set_purchase_record.data.timestamp,
            level=set_purchase_record.data.level,
            source=PurchaseSource.ADMIN,
            launch_record=launch_record,
            sale_option_record=sale_option_record,
            purchase_record=purchase_record,
            batch_index=batch_index,
        )
