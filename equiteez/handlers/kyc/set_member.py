from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_member import SetMemberParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_member(
    ctx: HandlerContext,
    set_member: TezosTransaction[SetMemberParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = set_member.data.target_address

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Update record
    for item in set_member.parameter.root:
        user, _ = await models.EquiteezUser.get_or_create(address=item.memberAddress)
        await user.save()
        if item.updateType == "remove":
            member = await models.KycMember.get_or_none(kyc=kyc, user=user)
            if member:
                member.membership_tier = None
                await member.save()
        else:
            member, _ = await models.KycMember.get_or_create(kyc=kyc, user=user)
            member.membership_tier = item.membershipTier
            await member.save()
