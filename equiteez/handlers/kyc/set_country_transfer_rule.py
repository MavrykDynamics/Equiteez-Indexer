from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_country_transfer_rule import (
    SetCountryTransferRuleParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_country_transfer_rule(
    ctx: HandlerContext,
    set_country_transfer_rule: TezosTransaction[
        SetCountryTransferRuleParameter, KycStorage
    ],
) -> None:
    await sync_kyc_operation(ctx, set_country_transfer_rule)
