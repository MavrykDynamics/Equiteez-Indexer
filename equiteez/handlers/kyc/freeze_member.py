from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.freeze_member import FreezeMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def freeze_member(
    ctx: HandlerContext,
    freeze_member: TezosTransaction[FreezeMemberParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = freeze_member.data.target_address
    member_ledger   = freeze_member.storage.memberLedger

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    for member_address in member_ledger:
        member_record       = member_ledger[member_address]
        frozen              = member_record.frozen
        user, _             = await models.EquiteezUser.get_or_create(
            address = member_address
        )
        await user.save()
        member , _          = await models.KycMember.get_or_create(
            kyc     = kyc,
            user    = user
        )
        member.frozen    = frozen
        await member.save()
