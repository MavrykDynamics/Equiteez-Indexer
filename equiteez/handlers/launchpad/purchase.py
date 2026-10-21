from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez.types.launchpad.tezos_parameters.purchase import PurchaseParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import record_user_purchase_batch


async def purchase(
    ctx: HandlerContext,
    purchase: TezosTransaction[PurchaseParameter, LaunchpadStorage],
) -> None:
    await record_user_purchase_batch(
        ctx, purchase, [(0, purchase.parameter, purchase.data.sender_address)]
    )
