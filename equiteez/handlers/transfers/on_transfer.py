import logging
from typing import Optional

from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez.types.base_token.tezos_parameters.transfer import TransferParameter
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.types.quote_token.tezos_storage import QuoteTokenStorage
from equiteez.utils.transfer_utils import record_user_transfers

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
    # Internal transfers are contract flows (orderbook escrow, launchpad
    # payments and issuance), not user movements
    if transfer.data.nonce is not None:
        return

    transfer_param = parse_transfer_param(transfer, transfer.data.level)
    if not transfer_param:
        return

    await record_user_transfers(
        ctx, transfer.data.target_address, transfer_param.root, transfer.data
    )
