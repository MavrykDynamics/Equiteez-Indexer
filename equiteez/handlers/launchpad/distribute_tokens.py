from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.distribute_tokens import (
    DistributeTokensParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def distribute_tokens(
    ctx: HandlerContext,
    distribute_tokens: TezosTransaction[DistributeTokensParameter, LaunchpadStorage],
) -> None:
    """Sync total_distributed from storage (idempotent on replay) and emit
    one history event per item. The unique constraint on the event table is
    the safety net against duplicates."""
    address = distribute_tokens.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    ledger_by_key = {
        (item.key.string, item.key.address): item.value
        for item in distribute_tokens.storage.purchaseLedger
    }

    for batch_index, item in enumerate(distribute_tokens.parameter.root):
        launch = await models.LaunchpadLaunch.get_or_none(
            launchpad=launchpad, name=item.launchName
        )
        if not launch:
            continue

        user, _ = await models.EquiteezUser.get_or_create(address=item.userAddress)
        await user.save()

        purchase, _ = await models.LaunchpadPurchase.get_or_create(
            launch=launch, user=user
        )

        record = ledger_by_key.get((item.launchName, item.userAddress))
        new_total = (
            int(record.totalDistributed) if record else purchase.total_distributed
        )
        delta = max(0, new_total - purchase.total_distributed)
        purchase.total_distributed = new_total
        await purchase.save()

        if delta > 0:
            await models.LaunchpadDistributionEvent.get_or_create(
                operation_hash=distribute_tokens.data.hash,
                launch=launch,
                user=user,
                batch_index=batch_index,
                defaults={
                    "amount": delta,
                    "timestamp": distribute_tokens.data.timestamp,
                    "level": distribute_tokens.data.level,
                },
            )
