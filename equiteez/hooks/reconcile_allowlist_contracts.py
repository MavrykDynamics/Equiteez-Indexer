import logging
from typing import Callable

from dipdup.context import HookContext

from equiteez import models
from equiteez.utils.contract_allowlist import (
    BASE_TOKENS,
    KYC,
    ORDERBOOKS,
    SUPER_ADMINS,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.dynamic_index import (
    attach_index_base_token,
    attach_index_kyc,
    attach_index_orderbook,
    attach_index_super_admin,
)

logger = logging.getLogger(__name__)

_ALLOWLIST_KEY = {
    models.ContractType.BASE_TOKEN: BASE_TOKENS,
    models.ContractType.ORDERBOOK: ORDERBOOKS,
    models.ContractType.SUPER_ADMIN: SUPER_ADMINS,
    models.ContractType.KYC: KYC,
}

_ATTACH_INDEX_FN: dict[models.ContractType, Callable] = {
    models.ContractType.BASE_TOKEN: attach_index_base_token,
    models.ContractType.ORDERBOOK: attach_index_orderbook,
    models.ContractType.SUPER_ADMIN: attach_index_super_admin,
    models.ContractType.KYC: attach_index_kyc,
}


async def reconcile_allowlist_contracts(
    ctx: HookContext,
) -> None:
    logger.info("reconcile_allowlist_contracts: starting")

    allowed = await fetch_allowlist()
    if allowed is None:
        logger.warning("reconcile_allowlist_contracts: allowlist fetch failed, skipping")
        return

    pending = await models.TrackedContract.filter(
        status=models.ContractStatus.PENDING,
    ).all()

    if not pending:
        logger.info("reconcile_allowlist_contracts: no pending contracts")
        return

    reconciled = 0

    for contract in pending:
        key = _ALLOWLIST_KEY.get(contract.contract_type)
        if not key:
            continue

        if not allowlist_contains(allowed, key, contract.address):
            continue

        attach_fn = _ATTACH_INDEX_FN[contract.contract_type]
        registered = await attach_fn(ctx, contract.address, first_level=contract.first_level)

        if registered:
            if contract.contract_type == models.ContractType.BASE_TOKEN:
                from equiteez.utils.utils import register_token
                await register_token(ctx, contract.address)

            reconciled += 1
            logger.info(
                "Reconciled %s %s from level %d",
                contract.contract_type.name,
                contract.address,
                contract.first_level,
            )

    logger.info("reconcile_allowlist_contracts: done, %d new contract(s) registered", reconciled)
