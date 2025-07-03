from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.set_super_admin import (
    SetSuperAdminParameter,
)
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, MarketplaceStorage],
) -> None:
    breakpoint()
