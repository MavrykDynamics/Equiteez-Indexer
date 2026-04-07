import logging
from typing import Optional, Set

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models
from equiteez.models.shared import TransferType
from equiteez.types.base_token.tezos_parameters.transfer import TransferParameter
from equiteez.utils.configs import (
    get_liquidity_pool_addresses,
    get_maven_lending_addresses,
    get_quote_token_address,
)
from equiteez.utils.indexed_addresses import get_indexed_addresses
from equiteez.utils.utils import register_token

logger = logging.getLogger(__name__)


def resolve_transfer_type(from_addr: Optional[str], to_addr: Optional[str]) -> TransferType:
    if not from_addr:
        return TransferType.MINT
    if not to_addr:
        return TransferType.BURN
    return TransferType.TRANSFER


def is_user_transfer(
    from_addr: Optional[str],
    to_addr: Optional[str],
    token_addr: str,
    orderbook: Set[str],
    pools: Set[str],
    superadmins: Set[str],
    maven_lending: Set[str],
    quote_token: Optional[str],
    base_tokens: Set[str],
) -> bool:
    if not (from_addr and to_addr):
        return False

    addr_set = {from_addr, to_addr}

    if addr_set & orderbook and (token_addr == quote_token or token_addr in base_tokens):
        return False
    if addr_set & pools or addr_set & superadmins or addr_set & maven_lending:
        return False

    return True


async def get_or_create_user(address: str, connection=None) -> Optional[models.EquiteezUser]:
    if not address:
        return None
    kwargs = {"address": address}
    if connection:
        kwargs["using_db"] = connection
    user, _ = await models.EquiteezUser.get_or_create(**kwargs)
    return user


def parse_transfer_param(transaction: TezosTransaction, level: int) -> Optional[TransferParameter]:
    param = getattr(transaction, "parameter", None)
    if not param:
        logger.warning("No parameter found at level %d", level)
        return None

    try:
        if hasattr(param, "root"):
            return param
        raw_param = getattr(transaction, "parameter_json", param)
        return TransferParameter.model_validate(raw_param)
    except Exception as e:
        logger.error("Error parsing transfer parameter at level %d: %s", level, e)
        return None


async def on_transfer(ctx: HandlerContext, transaction: TezosTransaction) -> None:
    level = transaction.data.level
    timestamp = transaction.data.timestamp
    contract_address = transaction.data.target_address
    operation_hash = transaction.data.hash

    transfer_param = parse_transfer_param(transaction, level)
    if not transfer_param:
        return

    indexed = await get_indexed_addresses()
    orderbook = indexed.orderbook
    base_tokens = indexed.base_tokens
    superadmins = indexed.super_admins
    quote_token = get_quote_token_address()
    pools = set(get_liquidity_pool_addresses())
    maven_lending = set(get_maven_lending_addresses())

    for item in transfer_param.root:
        from_address = item.from_

        for tx in item.txs:
            to_address = tx.to_
            token_id = int(tx.token_id)
            amount = int(tx.amount)

            if not is_user_transfer(
                from_address,
                to_address,
                contract_address,
                orderbook,
                pools,
                superadmins,
                maven_lending,
                quote_token,
                base_tokens,
            ):
                continue

            token = await models.Token.get_or_none(
                address=contract_address,
                token_id=token_id,
            )
            base_token = None
            if not token:
                base_token = await register_token(ctx, contract_address)
                if not base_token:
                    logger.error(
                        "Failed to register token %s at level %d",
                        contract_address,
                        level,
                    )
                    continue

            if not token:
                token, _ = await models.Token.get_or_create(
                    address=contract_address,
                    token_id=token_id,
                )
                token.metadata = token.metadata or base_token.metadata
                token.token_metadata = token.token_metadata or base_token.token_metadata
                token.token_standard = token.token_standard or base_token.token_standard
                await token.save()

            sender = await get_or_create_user(from_address)
            receiver = await get_or_create_user(to_address)
            transfer_type = resolve_transfer_type(from_address, to_address)

            transfer = models.EquiteezUserTokenTransfer(
                from_user=sender,
                to_user=receiver,
                token=token,
                timestamp=timestamp,
                level=level,
                operation_hash=operation_hash,
                amount=amount,
                transfer_type=transfer_type,
            )

            await transfer.save()
