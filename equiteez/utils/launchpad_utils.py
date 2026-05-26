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
from equiteez.utils.utils import register_token


_LAUNCH_STATUS_MAP = {
    "ACTIVE": LaunchStatus.ACTIVE,
    "INACTIVE": LaunchStatus.INACTIVE,
    "PAUSED": LaunchStatus.PAUSED,
    "CLOSED": LaunchStatus.CLOSED,
}

_ISSUANCE_MAP = {
    "mint": TokenIssuanceType.MINT,
    "transfer": TokenIssuanceType.TRANSFER,
}

_DISTRIBUTION_MAP = {
    "auto": TokenDistributionType.AUTO,
    "manual": TokenDistributionType.MANUAL,
}


def parse_launch_status(value: str) -> LaunchStatus:
    return _LAUNCH_STATUS_MAP.get(value, LaunchStatus.ACTIVE)


def parse_issuance_type(value: str) -> TokenIssuanceType:
    return _ISSUANCE_MAP.get(value, TokenIssuanceType.TRANSFER)


def parse_distribution_type(value: str) -> TokenDistributionType:
    return _DISTRIBUTION_MAP.get(value, TokenDistributionType.AUTO)


def parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return parser.parse(value)


def payment_token_address(currency) -> Optional[str]:
    if hasattr(currency, "fa12") and currency.fa12:
        return currency.fa12
    if hasattr(currency, "fa2") and currency.fa2 is not None:
        return currency.fa2.tokenContractAddress
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
    token = await register_token(ctx=ctx, address=record.tokenContractAddress)

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
