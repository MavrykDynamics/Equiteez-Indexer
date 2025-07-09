from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.claim_super_admin import (
    ClaimSuperAdminParameter,
)
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, MarketplaceStorage],
) -> None:
    breakpoint()
