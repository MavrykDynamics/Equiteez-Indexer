import logging

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
    contract_name = f"{name_prefix}_{address}"
    index_name = f"{index_name_prefix}_{address}"

    logger.info(
        "Attaching index for %s %s (from level %d)",
        contract_type.name,
        address,
        first_level,
    )

    try:
        await ctx.add_contract(
            kind="tezos",
            name=contract_name,
            address=address,
            typename=typename,
        )
    except Exception as exc:
        logger.debug(
            "add_contract for %s %s skipped: %s", contract_type.name, address, exc
        )

    try:
        await ctx.add_index(
            name=index_name,
            template=template,
            values={template_key: contract_name},
            first_level=first_level,
        )
    except Exception as exc:
        logger.debug(
            "add_index for %s %s skipped: %s", contract_type.name, address, exc
        )
        return False

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
