from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.transfer_fees import (
    TransferFeesParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def transfer_fees(
    ctx: HandlerContext,
    transfer_fees: TezosTransaction[TransferFeesParameter, OrderbookStorage],
) -> None:
    # Fetch operations info
    address = transfer_fees.data.target_address
    fee_ledger = transfer_fees.storage.feeLedger

    # Get orderbook
    orderbook = await models.Orderbook.get(address=address)

    # Update fees
    for currency_name in fee_ledger:
        fee_record = fee_ledger[currency_name]
        fee_amount = fee_record.nat_0
        paid_fee = fee_record.nat_1
        currency, _ = await models.OrderbookCurrency.get_or_create(
            orderbook=orderbook, currency_name=currency_name
        )
        await currency.save()
        orderbook_fee = models.OrderbookFee(
            orderbook=orderbook,
            currency=currency,
            fee_amount=fee_amount,
            paid_fee=paid_fee,
        )
        await orderbook_fee.save()
