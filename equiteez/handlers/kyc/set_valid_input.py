from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_valid_input import SetValidInputParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_valid_input(
    ctx: HandlerContext,
    set_valid_input: TezosTransaction[SetValidInputParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = set_valid_input.data.target_address
    valid_inputs = set_valid_input.storage.validInputLedger

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Update records
    for category in valid_inputs:
        valid_input_list = valid_inputs[category]
        if category == "country":
            countries, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.COUNTRY
            )
            countries.valid_inputs = valid_input_list
            await countries.save()
        if category == "region":
            regions, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.REGION
            )
            regions.valid_inputs = valid_input_list
            await regions.save()
        if category == "investor_type":
            investor_types, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.INVESTOR_TYPE
            )
            investor_types.valid_inputs = valid_input_list
            await investor_types.save()
