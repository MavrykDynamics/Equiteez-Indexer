import logging
from datetime import datetime, timezone

from dipdup.context import DipDupContext

from equiteez import models
from equiteez.utils.indexed_addresses import invalidate_cache

logger = logging.getLogger(__name__)

BASE_TOKEN_TYPENAME = "base_token"
ORDERBOOK_TYPENAME = "orderbook"
SUPER_ADMIN_TYPENAME = "super_admin"
KYC_TYPENAME = "kyc"


async def _attach_index(
    ctx: DipDupContext,
    address: str,
    contract_type: models.ContractType,
    typename: str,
    name_prefix: str,
    index_name_prefix: str,
    template: str,
    template_key: str,
    first_level: int,
) -> bool:
    tracked = await models.TrackedContract.get_or_none(
        address=address,
        contract_type=contract_type,
    )

    if tracked and tracked.status == models.ContractStatus.INDEXED:
        logger.debug("%s %s already indexed, skipping", contract_type.name, address)
        return False

    contract_name = f"{name_prefix}_{address}"
    effective_level = tracked.first_level if tracked else first_level

    logger.info("Attaching index for %s %s (from level %d)", contract_type.name, address, effective_level)

    try:
        await ctx.add_contract(
            kind="tezos",
            name=contract_name,
            address=address,
            typename=typename,
        )
    except Exception as exc:
        logger.debug("add_contract for %s %s skipped: %s", contract_type.name, address, exc)

    await ctx.add_index(
        name=f"{index_name_prefix}_{address}",
        template=template,
        values={template_key: contract_name},
        first_level=effective_level,
    )

    now = datetime.now(timezone.utc)
    if tracked:
        tracked.status = models.ContractStatus.INDEXED
        tracked.indexed_at = now
        await tracked.save()
    else:
        await models.TrackedContract.create(
            address=address,
            contract_type=contract_type,
            first_level=first_level,
            status=models.ContractStatus.INDEXED,
            indexed_at=now,
        )

    invalidate_cache()
    logger.info("Index attached for %s %s", contract_type.name, address)
    return True


async def attach_index_base_token(
    ctx: DipDupContext,
    address: str,
    first_level: int = 0,
) -> bool:
    return await _attach_index(
        ctx=ctx,
        address=address,
        contract_type=models.ContractType.BASE_TOKEN,
        typename=BASE_TOKEN_TYPENAME,
        name_prefix="token",
        index_name_prefix="transfers",
        template="token_transfers_template",
        template_key="token_contract",
        first_level=first_level,
    )


async def attach_index_orderbook(
    ctx: DipDupContext,
    address: str,
    first_level: int = 0,
) -> bool:
    return await _attach_index(
        ctx=ctx,
        address=address,
        contract_type=models.ContractType.ORDERBOOK,
        typename=ORDERBOOK_TYPENAME,
        name_prefix="orderbook",
        index_name_prefix="orderbook",
        template="orderbook_template",
        template_key="orderbook_contract",
        first_level=first_level,
    )


async def attach_index_super_admin(
    ctx: DipDupContext,
    address: str,
    first_level: int = 0,
) -> bool:
    return await _attach_index(
        ctx=ctx,
        address=address,
        contract_type=models.ContractType.SUPER_ADMIN,
        typename=SUPER_ADMIN_TYPENAME,
        name_prefix="super_admin",
        index_name_prefix="super_admin",
        template="super_admin_template",
        template_key="super_admin_contract",
        first_level=first_level,
    )


async def attach_index_kyc(
    ctx: DipDupContext,
    address: str,
    first_level: int = 0,
) -> bool:
    return await _attach_index(
        ctx=ctx,
        address=address,
        contract_type=models.ContractType.KYC,
        typename=KYC_TYPENAME,
        name_prefix="kyc",
        index_name_prefix="kyc",
        template="kyc_template",
        template_key="kyc_contract",
        first_level=first_level,
    )
