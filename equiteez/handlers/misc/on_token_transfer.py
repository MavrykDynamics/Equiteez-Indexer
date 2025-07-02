from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTokenTransferData
from equiteez import models as models
from dateutil import parser 

async def on_token_transfer(
    ctx: HandlerContext,
    token_transfer: TezosTokenTransferData,
) -> None:
    # Fetch operation info
    level               = token_transfer.level
    timestamp           = parser.parse(token_transfer.timestamp)
    contract_address    = token_transfer.contract_address
    from_address        = token_transfer.from_address
    to_address          = token_transfer.to_address
    amount              = token_transfer.amount
    transfer_type       = models.TransferType.TRANSFER

    # Register token
    token           = await models.Token.get_or_none(
        address = contract_address
    )
    if not token:
        return

    # Create the transfer record
    sender              = None
    if from_address:
        sender, _       = await models.EquiteezUser.get_or_create(
            address = from_address
        )
        await sender.save()
    else:
        transfer_type   = models.TransferType.MINT
    receiver            = None
    if to_address:
        receiver, _     = await models.EquiteezUser.get_or_create(
            address = to_address
        )
        await receiver.save()
    else:
        transfer_type   = models.TransferType.BURN
    token_transfer_record   = models.EquiteezUserTokenTransfer(
        from_user       = sender,
        to_user         = receiver,
        token           = token,
        timestamp       = timestamp,
        level           = level,
        transfer_type   = transfer_type,
        amount          = amount
    )
    await token_transfer_record.save()
