from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_country_transfer_rule import SetCountryTransferRuleParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_country_transfer_rule(
    ctx: HandlerContext,
    set_country_transfer_rule: TezosTransaction[SetCountryTransferRuleParameter, KycStorage],
) -> None:
    breakpoint()