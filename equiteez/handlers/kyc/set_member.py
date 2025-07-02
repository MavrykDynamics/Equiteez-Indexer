from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_member import SetMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from dateutil import parser

async def set_member(
    ctx: HandlerContext,
    set_member: TezosTransaction[SetMemberParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = set_member.data.target_address
    member_ledger   = set_member.storage.memberLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for member_address in member_ledger:
        member_record           = member_ledger[member_address]
        country                 = member_record.country
        region                  = member_record.region
        investor_type           = member_record.investorType
        frozen                  = member_record.frozen
        kyc_registrar_address   = member_record.kycRegistrar
        registrar, _            = await models.EquiteezUser.get_or_create(
            address = kyc_registrar_address
        )
        await registrar.save()
        kyc_registrar           = await models.KycRegistrar.get(
            kyc     = kyc,
            user    = registrar
        )
        user, _                 = await models.EquiteezUser.get_or_create(
            address = member_address
        )
        await user.save()
        member , _              = await models.KycMember.get_or_create(
            kyc     = kyc,
            user    = user
        )
        member.kyc_registrar    = kyc_registrar
        member.country          = country
        member.region           = region
        member.investor_type    = investor_type
        if member_record.expireAt:
            member.expire_at        = parser.parse(member_record.expireAt)
        member.frozen           = frozen
        await member.save()
