from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_kyc_registrar import SetKycRegistrarParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from dateutil import parser

async def set_kyc_registrar(
    ctx: HandlerContext,
    set_kyc_registrar: TezosTransaction[SetKycRegistrarParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = set_kyc_registrar.data.target_address
    kyc_registrars  = set_kyc_registrar.storage.kycRegistrarLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for registrar_address in kyc_registrars:
        kyc_registrar           = kyc_registrars[registrar_address]
        kyc_admins              = kyc_registrar.kycAdmins
        name                    = kyc_registrar.name
        members_verified        = kyc_registrar.membersVerified
        created_at              = parser.parse(kyc_registrar.createdAt)
        set_member_paused       = kyc_registrar.setMemberIsPaused
        freeze_member_paused    = kyc_registrar.freezeMemberIsPaused
        unfreeze_member_paused  = kyc_registrar.unfreezeMemberIsPaused
        user, _             = await models.EquiteezUser.get_or_create(
            address = registrar_address
        )
        await user.save()
        registrar , _   = await models.KycRegistrar.get_or_create(
            kyc     = kyc,
            user    = user
        )
        registrar.kyc_admins                = kyc_admins
        registrar.name                      = name
        registrar.members_verified          = members_verified
        registrar.created_at                = created_at
        registrar.set_member_paused         = set_member_paused
        registrar.freeze_member_paused      = freeze_member_paused
        registrar.unfreeze_member_paused    = unfreeze_member_paused
        await registrar.save()
