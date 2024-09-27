from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.sell_base_token import SellBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def sell_base_token(
    ctx: HandlerContext,
    sell_base_token: TezosTransaction[SellBaseTokenParameter, DodoMavStorage],
) -> None:
    ...