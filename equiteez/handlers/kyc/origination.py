from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.contract_allowlist import (
    KYC,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.kyc_utils import sync_kyc
from equiteez.utils.utils import get_contract_metadata


async def origination(
    ctx: HandlerContext,
    kyc_origination: TezosOrigination[KycStorage],
) -> None:
    # Fetch operation info
    address = kyc_origination.data.originated_contract_address

    if not address:
        return

    # Prepare the kyc
    kyc, _ = await models.Kyc.get_or_create(address=address)
    kyc.metadata = await get_contract_metadata(ctx=ctx, address=address)
    allowlist = await fetch_allowlist()
    kyc.in_allowlist = allowlist_contains(allowlist, KYC, address)

    # Origination storage carries every big map key
    await sync_kyc(ctx, kyc, kyc_origination.storage, kyc_origination.data)
