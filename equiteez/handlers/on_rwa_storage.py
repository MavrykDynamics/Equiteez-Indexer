from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOperationData

from equiteez import models
from equiteez.types.launchpad.tezos_storage import LaunchLedger
from equiteez.utils.launchpad_utils import upsert_launch_from_record
from equiteez.utils.rwa_supply import sync_token_supply


def matches(contract, operation: TezosOperationData) -> bool:
    return bool(
        (contract.address and operation.target_address == contract.address)
        or (
            contract.resolved_code_hash is not None
            and operation.target_code_hash == contract.resolved_code_hash
        )
    )


async def on_rwa_storage(ctx: HandlerContext, operation: TezosOperationData) -> None:
    # Untyped patterns cover mint/burn and calls through the root default
    # entrypoint without generating parameter types. Check the destination:
    # code-hash subscriptions may also deliver other contracts' internal calls.
    if operation.status != "applied":
        return
    if matches(ctx.config.contracts["token_watcher"], operation):
        await sync_token_supply(operation)
    elif matches(ctx.config.contracts["launchpad_watcher"], operation):
        launchpad = await models.Launchpad.get(address=operation.target_address)
        for diff in operation.diffs:
            if diff.get("path") not in ("launchLedger", "treasuryLedger"):
                continue
            if diff["action"] not in ("add_key", "update_key"):
                raise ValueError("Unsupported launchpad supply mapping change")
            content = diff["content"]
            if diff["path"] == "treasuryLedger":
                await models.LaunchpadTreasury.update_or_create(
                    launchpad=launchpad,
                    name=content["key"],
                    defaults={"address": content["value"]},
                )
            else:
                await upsert_launch_from_record(
                    ctx,
                    launchpad,
                    content["key"],
                    LaunchLedger.model_validate(content["value"]),
                )
