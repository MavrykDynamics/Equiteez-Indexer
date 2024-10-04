from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTokenTransferData
from equiteez import models as models
from equiteez.utils.utils import register_token


async def on_token_transfer(
    ctx: HandlerContext,
    token_transfer: TezosTokenTransferData,
) -> None:
    # Fetch operation info
    level               = token_transfer.level
    timestamp           = token_transfer.timestamp
    contract_address    = token_transfer.contract_address
    from_address        = token_transfer.from_address
    to_address          = token_transfer.to_address
    amount              = token_transfer.amount

    # Register token
    token               = await register_token(
        ctx     = ctx,
        address = contract_address
    )

    # Create the transfer record
    sender              = None
    if from_address:
        sender, _       = await models.EquiteezUser.get_or_create(
            address = from_address
        )
        await sender.save()
    receiver            = None
    if to_address:
        receiver, _     = await models.EquiteezUser.get_or_create(
            address = to_address
        )
        await receiver.save()
    token_transfer_record   = models.EquiteezUserTokenTransfer(
        from_user   = sender,
        to_user     = receiver,
        token       = token,
        timestamp   = timestamp,
        level       = level,
        amount      = amount
    )
    await token_transfer_record.save()
