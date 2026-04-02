import logging
from typing import Optional, Tuple

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosBigMapDiff
from tortoise.transactions import in_transaction

from equiteez import models
from equiteez.utils.utils import register_token

logger = logging.getLogger(__name__)


def _parse_owner_and_token_id(key) -> Tuple[Optional[str], int]:
    if key is None:
        return None, 0
    if hasattr(key, "owner") and getattr(key, "owner", None) is not None:
        tid = 0
        if hasattr(key, "token_id") and key.token_id is not None:
            tid = int(key.token_id)
        return key.owner, tid
    if hasattr(key, "root"):
        return key.root, 0
    return None, 0


def _balance_from_value(value) -> Optional[int]:
    if value is None:
        return None
    if hasattr(value, "root"):
        return int(value.root)
    return int(value)


async def on_balance_update(
    ctx: HandlerContext,
    data_ledger: TezosBigMapDiff,
) -> None:
    if data_ledger.key is None:
        return

    owner_address, token_id = _parse_owner_and_token_id(data_ledger.key)
    if not owner_address:
        return

    contract_address = data_ledger.data.contract_address
    level = data_ledger.data.level
    timestamp = data_ledger.data.timestamp

    balance_raw = _balance_from_value(getattr(data_ledger, "value", None))
    if balance_raw is None:
        return

    async with in_transaction() as connection:
        token = await models.Token.get_or_none(
            address=contract_address,
            token_id=token_id,
            using_db=connection,
        )
        if not token:
            base_token = await register_token(ctx, contract_address)
            if not base_token:
                logger.error("Failed to register token %s", contract_address)
                return

            token, _ = await models.Token.get_or_create(
                address=contract_address,
                token_id=token_id,
                using_db=connection,
            )
            token.metadata = token.metadata or base_token.metadata
            token.token_metadata = token.token_metadata or base_token.token_metadata
            token.token_standard = token.token_standard or base_token.token_standard
            await token.save(using_db=connection)

        user, _ = await models.EquiteezUser.get_or_create(
            address=owner_address,
            using_db=connection,
        )

        user_balance, created = await models.EquiteezUserBalance.get_or_create(
            user=user,
            token=token,
            defaults={"balance": balance_raw},
            using_db=connection,
        )

        old_balance = 0 if created else int(user_balance.balance)  # noqa: F841 — for EventsOutbox when re-enabled

        if not created:
            user_balance.balance = balance_raw
            await user_balance.save(using_db=connection)

        # from equiteez.shared import AggregateType, EventType
        # outbox_event = await models.EventsOutbox.create_event(
        #     event_type=EventType.BALANCE_UPDATED,
        #     aggregate_type=AggregateType.ACCOUNT,
        #     aggregate_id=f"{owner_address}:{contract_address}:{token.token_id}",
        #     payload={
        #         "user_address": owner_address,
        #         "token_address": contract_address,
        #         "token_id": token.token_id,
        #         "old_balance": str(old_balance),
        #         "new_balance": str(balance_raw),
        #         "balance_change": str(balance_raw - old_balance),
        #         "level": level,
        #         "timestamp": timestamp.isoformat(),
        #     },
        #     occurred_at=timestamp,
        # )
        # await outbox_event.save(using_db=connection)
