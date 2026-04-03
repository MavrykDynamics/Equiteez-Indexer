"""
In-memory cache of INDEXED contract addresses for transfer filtering.

Loaded on first access from TrackedContract(status=INDEXED), invalidated whenever
attach_index_* promotes TrackedContract to INDEXED.  DipDup is single-threaded async,
so no locking is needed.
"""
import logging
from typing import NamedTuple, Optional, Set

from equiteez import models

logger = logging.getLogger(__name__)


class IndexedAddresses(NamedTuple):
    orderbook: Set[str]
    base_tokens: Set[str]
    super_admins: Set[str]


_cache: Optional[IndexedAddresses] = None


def invalidate_cache() -> None:
    global _cache
    _cache = None
    logger.debug("indexed_addresses cache invalidated")


async def _load_from_db() -> IndexedAddresses:
    orderbook: Set[str] = set()
    base_tokens: Set[str] = set()
    super_admins: Set[str] = set()

    try:
        rows = await models.TrackedContract.filter(
            status=models.ContractStatus.INDEXED,
            contract_type__in=[
                models.ContractType.BASE_TOKEN,
                models.ContractType.ORDERBOOK,
                models.ContractType.SUPER_ADMIN,
            ],
        ).values_list("contract_type", "address")
    except Exception as exc:
        logger.debug("tracked_contract query failed (first boot?): %s", exc)
        return IndexedAddresses(orderbook, base_tokens, super_admins)

    for ctype, addr in rows:
        if not addr:
            continue
        if ctype == models.ContractType.BASE_TOKEN:
            base_tokens.add(addr)
        elif ctype == models.ContractType.ORDERBOOK:
            orderbook.add(addr)
        elif ctype == models.ContractType.SUPER_ADMIN:
            super_admins.add(addr)

    logger.debug(
        "indexed_addresses loaded: orderbooks=%d base_tokens=%d super_admins=%d",
        len(orderbook), len(base_tokens), len(super_admins),
    )
    return IndexedAddresses(orderbook, base_tokens, super_admins)


async def get_indexed_addresses() -> IndexedAddresses:
    global _cache
    if _cache is None:
        _cache = await _load_from_db()
    return _cache
