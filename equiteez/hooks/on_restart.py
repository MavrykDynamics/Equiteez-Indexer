import logging

from dipdup.context import HookContext

from equiteez import models

logger = logging.getLogger(__name__)

_TYPENAME = {
    models.ContractType.BASE_TOKEN: "base_token",
    models.ContractType.ORDERBOOK: "orderbook",
    models.ContractType.SUPER_ADMIN: "super_admin",
    models.ContractType.KYC: "kyc",
}

_PREFIX = {
    models.ContractType.BASE_TOKEN: "token",
    models.ContractType.ORDERBOOK: "orderbook",
    models.ContractType.SUPER_ADMIN: "super_admin",
    models.ContractType.KYC: "kyc",
}


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql("on_restart")

    try:
        contracts = await models.TrackedContract.filter(
            status=models.ContractStatus.INDEXED,
        ).all()
    except Exception as exc:
        logger.debug("tracked_contract table not ready yet: %s", exc)
        return

    counts = {k: 0 for k in _TYPENAME}

    for contract in contracts:
        ctype = contract.contract_type
        typename = _TYPENAME.get(ctype)
        prefix = _PREFIX.get(ctype)
        if not typename:
            continue

        contract_name = f"{prefix}_{contract.address}"
        try:
            await ctx.add_contract(
                kind="tezos",
                name=contract_name,
                address=contract.address,
                typename=typename,
            )
        except Exception as exc:
            logger.debug("Contract %s already registered: %s", contract.address, exc)

        counts[ctype] += 1

    logger.info(
        "Restored indexed contracts: tokens=%d orderbooks=%d super_admin=%d kyc=%d",
        counts[models.ContractType.BASE_TOKEN],
        counts[models.ContractType.ORDERBOOK],
        counts[models.ContractType.SUPER_ADMIN],
        counts[models.ContractType.KYC],
    )
