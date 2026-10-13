from dipdup.context import HookContext

from equiteez.hooks.update_allowlist_status import update_allowlist_status


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql("on_restart")
    # `dipdup schema init` invokes this hook before registering transactions.
    async with ctx.transactions.register():
        await update_allowlist_status(ctx)
