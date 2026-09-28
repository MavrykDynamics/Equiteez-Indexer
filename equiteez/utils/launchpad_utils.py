from datetime import datetime
from typing import Optional

from dateutil import parser

from equiteez import models as models
from equiteez.models.launchpad import (
    LaunchStatus,
    PurchaseSource,
    TokenDistributionType,
    TokenIssuanceType,
)
from equiteez.types.launchpad.tezos_storage import Config, LaunchpadStorage
from equiteez.utils.permits import permit_action, permit_signer
from equiteez.utils.utils import NATIVE_MAV_ADDRESS, register_token


_LAUNCH_STATUS_MAP = {
    "ACTIVE": LaunchStatus.ACTIVE,
    "INACTIVE": LaunchStatus.INACTIVE,
    "PAUSED": LaunchStatus.PAUSED,
    "CLOSED": LaunchStatus.CLOSED,
}

# The contract stores these uppercase: _verifyValidTokenIssuanceType accepts
# only "MINT" / "TRANSFER" and _verifyValidTokenDistributionType only
# "AUTO" / "MANUAL" (launchpadHelpers.ligo). Lookups are case-insensitive
# for safety.
_ISSUANCE_MAP = {
    "MINT": TokenIssuanceType.MINT,
    "TRANSFER": TokenIssuanceType.TRANSFER,
}

_DISTRIBUTION_MAP = {
    "AUTO": TokenDistributionType.AUTO,
    "MANUAL": TokenDistributionType.MANUAL,
}


def parse_launch_status(value: str) -> LaunchStatus:
    return _LAUNCH_STATUS_MAP.get(value.upper(), LaunchStatus.ACTIVE)


def parse_issuance_type(value: str) -> TokenIssuanceType:
    return _ISSUANCE_MAP.get(value.upper(), TokenIssuanceType.TRANSFER)


def parse_distribution_type(value: str) -> TokenDistributionType:
    return _DISTRIBUTION_MAP.get(value.upper(), TokenDistributionType.AUTO)


def parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return parser.parse(value)


def payment_token_address(currency) -> Optional[str]:
    if hasattr(currency, "fa12") and currency.fa12:
        return currency.fa12
    if hasattr(currency, "fa2") and currency.fa2 is not None:
        return currency.fa2.tokenContractAddress
    # tokenType has a third variant: native Mav (an empty record on-chain);
    # resolves to the NATIVE_MAV_ADDRESS pseudo-token so payments keep a Token link
    if hasattr(currency, "mav") and currency.mav is not None:
        return NATIVE_MAV_ADDRESS
    return None


async def apply_purchase(
    ctx,
    launchpad: "models.Launchpad",
    launch_name: str,
    user_address: str,
    sale_option_name: str,
    payment_name: str,
    event_amount: int,
    operation_hash: Optional[str],
    timestamp: datetime,
    level: int,
    source: PurchaseSource,
    *,
    launch_record,
    sale_option_record,
    purchase_record,
    batch_index: int = 0,
) -> None:
    launch = await models.LaunchpadLaunch.get(launchpad=launchpad, name=launch_name)
    sale_option = await models.LaunchpadSaleOption.get(
        launch=launch, name=sale_option_name
    )

    user, _ = await models.EquiteezUser.get_or_create(address=user_address)
    await user.save()

    launch.total_bought = int(launch_record.totalBought)
    await launch.save()

    sale_option.total_bought = int(sale_option_record.totalBought)
    await sale_option.save()

    purchase, _ = await models.LaunchpadPurchase.get_or_create(launch=launch, user=user)
    purchase.total_purchased = int(purchase_record.totalPurchased)
    purchase.total_distributed = int(purchase_record.totalDistributed)
    await purchase.save()

    by_option, _ = await models.LaunchpadPurchaseByOption.get_or_create(
        purchase=purchase, sale_option=sale_option
    )
    by_option.amount = int(purchase_record.purchased.get(sale_option_name, 0))
    await by_option.save()

    payment = (
        await models.LaunchpadSaleOptionPayment.filter(
            sale_option=sale_option, name=payment_name
        )
        .prefetch_related("token")
        .first()
    )
    payment_token = payment.token if payment else None

    # get_or_create on the unique_together key — no-op on reorg replay
    await models.LaunchpadPurchaseEvent.get_or_create(
        operation_hash=operation_hash,
        launch=launch,
        user=user,
        sale_option=sale_option,
        source=source,
        batch_index=batch_index,
        defaults={
            "payment_name": payment_name,
            "payment_token": payment_token,
            "amount": event_amount,
            "timestamp": timestamp,
            "level": level,
        },
    )


async def upsert_launch_from_record(
    ctx,
    launchpad: "models.Launchpad",
    name: str,
    record,
) -> "models.LaunchpadLaunch":
    token = await register_token(
        ctx=ctx, address=record.tokenContractAddress, token_id=int(record.tokenId)
    )

    defaults = {
        "status": parse_launch_status(record.status),
        "token_issuance_type": parse_issuance_type(record.tokenIssuanceType),
        "token_distribution_type": parse_distribution_type(
            record.tokenDistributionType
        ),
        "token": token,
        "purchase_fee_percent": int(record.purchaseFeePercent),
        "max_amount_cap": int(record.maxAmountCap),
        "total_bought": int(record.totalBought),
        "sale_start": parse_ts(record.saleStart),
        "sale_end": parse_ts(record.saleEnd),
        "sale_closed": parse_ts(record.saleClosed),
        "is_paused": record.isPaused,
        "enable_kyc": record.enableKyc,
    }

    launch, created = await models.LaunchpadLaunch.get_or_create(
        launchpad=launchpad, name=name, defaults=defaults
    )
    if not created:
        for k, v in defaults.items():
            setattr(launch, k, v)
        await launch.save()
    return launch


async def upsert_sale_option(
    ctx,
    launch: "models.LaunchpadLaunch",
    name: str,
    record,
) -> "models.LaunchpadSaleOption":
    defaults = {
        "total_bought": int(record.totalBought),
        "max_amount_cap": (
            int(record.maxAmountCap) if record.maxAmountCap is not None else None
        ),
        "is_paused": record.isPaused,
        "is_removed": False,
        "sale_start": parse_ts(record.saleStart),
        "sale_end": parse_ts(record.saleEnd),
    }

    sale_option, created = await models.LaunchpadSaleOption.get_or_create(
        launch=launch, name=name, defaults=defaults
    )
    if not created:
        for k, v in defaults.items():
            setattr(sale_option, k, v)
        await sale_option.save()

    seen_tier_names: set[str] = set()
    for tier_name, tier_record in record.allowedMembershipTiers.items():
        seen_tier_names.add(tier_name)
        tier_defaults = {
            "min_purchase_amount": (
                int(tier_record.minPurchaseAmount)
                if tier_record.minPurchaseAmount is not None
                else None
            ),
            "max_amount_per_wallet_total": (
                int(tier_record.maxAmountPerWalletTotal)
                if tier_record.maxAmountPerWalletTotal is not None
                else None
            ),
        }
        tier, tier_created = await models.LaunchpadSaleOptionTier.get_or_create(
            sale_option=sale_option, name=tier_name, defaults=tier_defaults
        )
        if not tier_created:
            for k, v in tier_defaults.items():
                setattr(tier, k, v)
            await tier.save()

    await (
        models.LaunchpadSaleOptionTier.filter(sale_option=sale_option)
        .exclude(name__in=list(seen_tier_names))
        .delete()
    )

    seen_payment_names: set[str] = set()
    for payment_name, payment_record in record.payments.items():
        seen_payment_names.add(payment_name)
        token_addr = payment_token_address(payment_record.currency)
        payment, _ = await models.LaunchpadSaleOptionPayment.get_or_create(
            sale_option=sale_option, name=payment_name
        )

        await payment.fetch_related("token")
        current_addr = payment.token.address if payment.token else None
        if token_addr != current_addr:
            payment.token = (
                await register_token(ctx=ctx, address=token_addr)
                if token_addr
                else None
            )
        payment.price = int(payment_record.price)
        await payment.save()

    await (
        models.LaunchpadSaleOptionPayment.filter(sale_option=sale_option)
        .exclude(name__in=list(seen_payment_names))
        .delete()
    )

    return sale_option


def apply_launchpad_config(launchpad: "models.Launchpad", config: Config) -> None:
    launchpad.permit_default_expiry_duration = int(config.permitDefaultExpiryDuration)
    launchpad.permit_max_expiry_duration = int(config.permitMaxExpiryDuration)


async def sync_launches(
    ctx,
    launchpad: "models.Launchpad",
    storage: LaunchpadStorage,
) -> None:
    """
    Mirror every launch the operation wrote. A launch record carries its full
    saleOptions map, so options missing from it were dropped on-chain
    (updateTokenLaunch replaces the map wholesale) and get flagged removed.
    """
    for launch_name, record in storage.launchLedger.items():
        launch = await upsert_launch_from_record(ctx, launchpad, launch_name, record)
        for option_name, option_record in record.saleOptions.items():
            await upsert_sale_option(ctx, launch, option_name, option_record)
        await (
            models.LaunchpadSaleOption.filter(launch=launch, is_removed=False)
            .exclude(name__in=list(record.saleOptions))
            .update(is_removed=True)
        )


async def record_purchase(
    ctx,
    launchpad: "models.Launchpad",
    storage: LaunchpadStorage,
    purchase,
    user_address: str,
    operation_hash: Optional[str],
    timestamp: datetime,
    level: int,
    batch_index: int = 0,
) -> None:
    """
    One on-chain purchase: the direct entrypoint (buyer = sender) or a
    PermitPurchase action (buyer = permit signer). `purchase` is the
    purchaseActionType payload.
    """
    launch_name = purchase.launchName
    sale_option_name = purchase.saleOption

    launch_record = storage.launchLedger.get(launch_name)
    if launch_record is None:
        ctx.logger.warning("purchase: launch %s not in storage; skipping", launch_name)
        return

    sale_option_record = launch_record.saleOptions.get(sale_option_name)
    if sale_option_record is None:
        ctx.logger.warning(
            "purchase: sale option %s not in launch %s storage; skipping",
            sale_option_name,
            launch_name,
        )
        return

    purchase_record = None
    for item in storage.purchaseLedger:
        if item.key.string == launch_name and item.key.address == user_address:
            purchase_record = item.value
            break

    if purchase_record is None:
        ctx.logger.warning(
            "purchase: no ledger entry for (%s, %s); skipping",
            launch_name,
            user_address,
        )
        return

    await apply_purchase(
        ctx=ctx,
        launchpad=launchpad,
        launch_name=launch_name,
        user_address=user_address,
        sale_option_name=sale_option_name,
        payment_name=purchase.payment,
        event_amount=int(purchase.amount),
        operation_hash=operation_hash,
        timestamp=timestamp,
        level=level,
        source=PurchaseSource.USER,
        launch_record=launch_record,
        sale_option_record=sale_option_record,
        purchase_record=purchase_record,
        batch_index=batch_index,
    )


async def record_permit_batch(ctx, transaction) -> None:
    """
    executePermit / permitAndExecute run PermitPurchase through the purchase
    lambda with the signer as buyer; the storage effects (ledgers, token
    issuance) are those of a direct purchase by the signer.
    """
    launchpad = await models.Launchpad.get(address=transaction.data.target_address)
    for batch_index, item in enumerate(transaction.parameter.root):
        name, payload = permit_action(item)
        if name != "permitPurchase":
            continue
        await record_purchase(
            ctx,
            launchpad,
            transaction.storage,
            payload,
            user_address=permit_signer(item),
            operation_hash=transaction.data.hash,
            timestamp=transaction.data.timestamp,
            level=transaction.data.level,
            batch_index=batch_index,
        )
