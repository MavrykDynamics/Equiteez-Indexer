from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_enable_kyc import SetEnableKycParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_enable_kyc(
    ctx: HandlerContext,
    set_enable_kyc: TezosTransaction[SetEnableKycParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = set_enable_kyc.data.target_address
    enable_kyc = set_enable_kyc.storage.enableKyc

    # Update kyc
    kyc = await models.Kyc.get(address=address)
    kyc.enable_kyc = enable_kyc
    await kyc.save()
