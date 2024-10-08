from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, KycStorage],
) -> None:
    breakpoint()