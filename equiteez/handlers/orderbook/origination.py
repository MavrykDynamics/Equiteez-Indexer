from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.contract_allowlist import (
    ORDERBOOKS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.orderbook_utils import (
    apply_orderbook_config,
    apply_orderbook_market_state,
    record_order_events,
    sync_book_maps,
    sync_currencies,
    sync_fee_ledger,
)
from equiteez.utils.utils import get_contract_metadata, register_token


async def origination(
    ctx: HandlerContext,
    orderbook_origination: TezosOrigination[OrderbookStorage],
) -> None:
    # Fetch operation info
    address = orderbook_origination.data.originated_contract_address

    if not address:
        return

    storage = orderbook_origination.storage

    # Get KYC
    kyc, _ = await models.Kyc.get_or_create(address=storage.membershipKycAddress)

    # Prepare the orderbook
    orderbook, _ = await models.Orderbook.get_or_create(address=address)
    orderbook.super_admin = storage.superAdmin
    orderbook.new_super_admin = storage.newSuperAdmin
    orderbook.kyc = kyc
    orderbook.rwa_token_decimals = int(storage.rwaTokenDecimals)
    apply_orderbook_config(orderbook, storage.config)
    apply_orderbook_market_state(orderbook, storage)

    # Get RWA Token
    orderbook.rwa_token = await register_token(ctx=ctx, address=storage.rwaTokenAddress)

    # Get contract metadata
    orderbook.metadata = await get_contract_metadata(ctx=ctx, address=address)

    allowlist = await fetch_allowlist()
    orderbook.in_allowlist = allowlist_contains(allowlist, ORDERBOOKS, address)

    # Save the orderbook
    await orderbook.save()

    # Currencies, fees and the (normally empty) book
    await sync_currencies(ctx, orderbook, storage)
    await sync_fee_ledger(orderbook, storage)
    await sync_book_maps(orderbook, storage)

    # Save the entrypoints status
    for entrypoint, paused in storage.pauseLedger.items():
        entrypoint_status, _ = await models.OrderbookEntrypointStatus.get_or_create(
            contract=orderbook, entrypoint=entrypoint
        )
        entrypoint_status.paused = paused
        await entrypoint_status.save()

    # Orders originated with the contract, if any
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=storage,
        intent=models.OrderEventType.SEED,
        data=orderbook_origination.data,
    )
