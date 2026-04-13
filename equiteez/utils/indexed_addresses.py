"""
In-memory cache of contract addresses for transfer filtering.

Loaded on first access from domain tables (Token, Orderbook, SuperAdmin), invalidated
whenever attach_index_* registers a new index. DipDup is single-threaded async,
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
        base_tokens = set(await models.Token.all().values_list("address", flat=True))
        orderbook = set(await models.Orderbook.all().values_list("address", flat=True))
        super_admins = set(
            await models.SuperAdmin.all().values_list("address", flat=True)
        )
    except Exception as exc:
        logger.debug("indexed_addresses query failed (first boot?): %s", exc)
        return IndexedAddresses(orderbook, base_tokens, super_admins)

    logger.debug(
        "indexed_addresses loaded: orderbooks=%d base_tokens=%d super_admins=%d",
        len(orderbook),
        len(base_tokens),
        len(super_admins),
    )
    return IndexedAddresses(orderbook, base_tokens, super_admins)


async def get_indexed_addresses() -> IndexedAddresses:
    global _cache
    if _cache is None:
        _cache = await _load_from_db()
    return _cache
