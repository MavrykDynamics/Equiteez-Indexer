from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.purchase import PurchaseParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import record_purchase


async def purchase(
    ctx: HandlerContext,
    purchase: TezosTransaction[PurchaseParameter, LaunchpadStorage],
) -> None:
    launchpad = await models.Launchpad.get(address=purchase.data.target_address)
    await record_purchase(
        ctx,
        launchpad,
        purchase.storage,
        purchase.parameter,
        user_address=purchase.data.sender_address,
        operation_hash=purchase.data.hash,
        timestamp=purchase.data.timestamp,
        level=purchase.data.level,
    )
