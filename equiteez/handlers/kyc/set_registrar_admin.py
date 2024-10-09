from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_registrar_admin import SetRegistrarAdminParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_registrar_admin(
    ctx: HandlerContext,
    set_registrar_admin: TezosTransaction[SetRegistrarAdminParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = set_registrar_admin.data.target_address
    kyc_registrars  = set_registrar_admin.storage.kycRegistrarLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for registrar_address in kyc_registrars:
        kyc_registrar           = kyc_registrars[registrar_address]
        kyc_admins              = kyc_registrar.kycAdmins
        user, _                 = await models.EquiteezUser.get_or_create(
            address = registrar_address
        )
        await user.save()
        registrar , _   = await models.KycRegistrar.get_or_create(
            kyc     = kyc,
            user    = user
        )
        registrar.kyc_admins                = kyc_admins
        await registrar.save()
