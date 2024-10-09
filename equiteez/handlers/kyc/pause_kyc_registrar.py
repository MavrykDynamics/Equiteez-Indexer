from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.pause_kyc_registrar import PauseKycRegistrarParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def pause_kyc_registrar(
    ctx: HandlerContext,
    pause_kyc_registrar: TezosTransaction[PauseKycRegistrarParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = pause_kyc_registrar.data.target_address
    kyc_registrars  = pause_kyc_registrar.storage.kycRegistrarLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for registrar_address in kyc_registrars:
        kyc_registrar           = kyc_registrars[registrar_address]
        user, _             = await models.EquiteezUser.get_or_create(
            address = registrar_address
        )
        await user.save()
        set_member_paused       = kyc_registrar.setMemberIsPaused
        registrar , _   = await models.KycRegistrar.get_or_create(
            kyc     = kyc,
            user    = user
        )
        registrar.set_member_paused         = set_member_paused
        await registrar.save()
