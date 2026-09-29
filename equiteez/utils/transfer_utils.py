import logging
from collections.abc import Iterable
from typing import Any

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOperationData

from equiteez import models as models
from equiteez.utils.utils import get_contract_token_metadata, register_token

logger = logging.getLogger(__name__)


def _is_user_to_user(from_address: str, to_address: str) -> bool:
    return not from_address.startswith("KT") and not to_address.startswith("KT")


async def _resolve_token(
    ctx: HandlerContext, contract_address: str, token_id: int, level: int
) -> "models.Token | None":
    token = await models.Token.get_or_none(address=contract_address, token_id=token_id)
    if token:
        return token

    base_token = await register_token(ctx, contract_address)
    if not base_token:
        logger.error("Failed to register token %s at level %d", contract_address, level)
        return None

    token, _ = await models.Token.get_or_create(
        address=contract_address, token_id=token_id
    )
    token.metadata = token.metadata or base_token.metadata
    if not token.token_metadata:
        if token_id == 0:
            token.token_metadata = base_token.token_metadata
        else:
            # The contract is multi-asset; fetch metadata for this token_id
            # instead of inheriting token 0's metadata.
            token.token_metadata = await get_contract_token_metadata(
                ctx=ctx, address=contract_address, token_id=str(token_id)
            )
    token.token_standard = token.token_standard or base_token.token_standard
    # Allowlist membership is per contract address; inherit it.
    token.in_allowlist = token.in_allowlist or base_token.in_allowlist
    await token.save()
    return token


async def record_user_transfers(
    ctx: HandlerContext,
    contract_address: str,
    items: Iterable[Any],
    data: TezosOperationData,
) -> None:
    """
    Record the user-to-user movements of FA2 `transfer` batch items
    (`{from_, txs: [{to_, token_id, amount}]}`), whether they come from the
    transfer entrypoint or a permitTransfer action.
    """
    for item in items:
        from_address = item.from_

        for tx in item.txs:
            to_address = tx.to_
            token_id = int(tx.token_id)
            amount = int(tx.amount)

            if not (from_address and to_address):
                continue

            # The contract skips zero-amount txs and, since the RWA token
            # invariants fix, self-transfers (no ledger change)
            if amount == 0 or from_address == to_address:
                continue

            if not _is_user_to_user(from_address, to_address):
                continue

            token = await _resolve_token(ctx, contract_address, token_id, data.level)
            if token is None:
                continue

            sender, _ = await models.EquiteezUser.get_or_create(address=from_address)
            receiver, _ = await models.EquiteezUser.get_or_create(address=to_address)

            await models.EquiteezUserTokenTransfer.create(
                from_user=sender,
                to_user=receiver,
                token=token,
                timestamp=data.timestamp,
                level=data.level,
                operation_hash=data.hash,
                amount=amount,
            )
