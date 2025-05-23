from dipdup.context import HookContext
from equiteez import models as models
from equiteez.utils.utils import register_token

async def refresh_tokens(
    ctx: HookContext,
) -> None:
    print("Refreshing all Equiteez tokens metadata")
    tokens = await models.Token.all()
    for token in tokens:
        await register_token(ctx, token.address)
