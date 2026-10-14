from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.update_config import (
    UpdateConfigParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import apply_orderbook_config


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, OrderbookStorage],
) -> None:
    orderbook = await models.Orderbook.get(address=update_config.data.target_address)
    apply_orderbook_config(orderbook, update_config.storage.config)
    await orderbook.save()
