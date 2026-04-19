import logging
from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.models.shared import TransferType
from equiteez.types.base_token.tezos_parameters.transfer import TransferParameter
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.types.quote_token.tezos_storage import QuoteTokenStorage
from equiteez.utils.indexed_addresses import get_indexed_addresses
from equiteez.utils.utils import register_token

logger = logging.getLogger(__name__)


def parse_transfer_param(
    transaction: TezosTransaction, level: int
) -> Optional[TransferParameter]:
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


async def on_transfer(
    ctx: HandlerContext,
    transfer: TezosTransaction[TransferParameter, BaseTokenStorage | QuoteTokenStorage],
) -> None:
    level = transfer.data.level
    timestamp = transfer.data.timestamp
    contract_address = transfer.data.target_address
    operation_hash = transfer.data.hash

    transfer_param = parse_transfer_param(transfer, level)
    if not transfer_param:
        return

    for item in transfer_param.root:
        from_address = item.from_

        for tx in item.txs:
            to_address = tx.to_
            token_id = int(tx.token_id)
            amount = int(tx.amount)

            if not (from_address and to_address) or from_address.startswith("KT"):
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

            sender, _ = await models.EquiteezUser.get_or_create(address=from_address)
            receiver, _ = await models.EquiteezUser.get_or_create(address=to_address)
            if not from_address:
                transfer_type = TransferType.MINT
            elif not to_address:
                transfer_type = TransferType.BURN
            else:
                transfer_type = TransferType.TRANSFER

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