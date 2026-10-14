from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez.types.base_token.tezos_parameters.execute_permit import (
    ExecutePermitParameter,
)
from equiteez.types.base_token.tezos_parameters.permit_and_execute import (
    PermitAndExecuteParameter,
)
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.types.quote_token.tezos_storage import QuoteTokenStorage
from equiteez.utils.permits import permit_action
from equiteez.utils.transfer_utils import record_user_transfers


async def on_permit(
    ctx: HandlerContext,
    permit: TezosTransaction[
        ExecutePermitParameter | PermitAndExecuteParameter,
        BaseTokenStorage | QuoteTokenStorage,
    ],
) -> None:
    """
    executePermit / permitAndExecute on an FA2 token (RWA tokens, the quote
    token).
    permitTransfer runs the same transfer as the entrypoint on the signer's
    behalf; the batch items name their owner (`from_`), so the signer is not
    needed. Operator updates and expiry settings are not indexed.
    """
    # Same rule as on_transfer: an internal call is a contract flow (a
    # launchpad or relayer contract executing the permit), not a user movement
    if permit.data.nonce is not None:
        return

    for item in permit.parameter.root:
        name, payload = permit_action(item)
        if name == "permitTransfer":
            await record_user_transfers(
                ctx, permit.data.target_address, payload, permit.data
            )
