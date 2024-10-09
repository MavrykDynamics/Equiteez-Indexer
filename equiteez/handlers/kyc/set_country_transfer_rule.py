from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_country_transfer_rule import SetCountryTransferRuleParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_country_transfer_rule(
    ctx: HandlerContext,
    set_country_transfer_rule: TezosTransaction[SetCountryTransferRuleParameter, KycStorage],
) -> None:
    # Fetch operation info
    address                         = set_country_transfer_rule.data.target_address
    country_transfer_rule_ledger    = set_country_transfer_rule.storage.countryTransferRuleLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for country in country_transfer_rule_ledger:
        transfer_rule               = country_transfer_rule_ledger[country]
        whitelist_countries         = transfer_rule.whitelistCountries
        blacklist_countries         = transfer_rule.blacklistCountries
        sending_frozen              = transfer_rule.sendingFrozen
        receiving_frozen            = transfer_rule.receivingFrozen
        country_transfer_rule, _    = await models.KycCountryTransferRule.get_or_create(
            kyc     = kyc,
            country = country
        )
        country_transfer_rule.whitelist_countries     = whitelist_countries
        country_transfer_rule.blacklist_countries     = blacklist_countries
        country_transfer_rule.sending_frozen          = sending_frozen
        country_transfer_rule.receiving_frozen        = receiving_frozen
        await country_transfer_rule.save()
