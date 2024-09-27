from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.buy_base_token import BuyBaseTokenParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def buy_base_token(
    ctx: HandlerContext,
    buy_base_token: TezosTransaction[BuyBaseTokenParameter, DodoMavStorage],
) -> None:
    ...