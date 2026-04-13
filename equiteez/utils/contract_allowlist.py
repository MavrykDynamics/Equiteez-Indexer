import logging
import os
from typing import Any, Dict, Optional, Set

import aiohttp

logger = logging.getLogger(__name__)

ORDERBOOKS = "orderbooks"
BASE_TOKENS = "base_tokens"
SUPER_ADMINS = "super_admins"
KYC = "kyc"

_KEYS = (ORDERBOOKS, BASE_TOKENS, SUPER_ADMINS, KYC)


def allowlist_url() -> str:
    url = os.getenv("CONTRACT_ALLOWLIST_URL", "").strip()
    if not url:
        raise RuntimeError(
            "CONTRACT_ALLOWLIST_URL env var is not set. "
            "Provide the URL for this network's allowlist JSON "
            "(e.g. https://test.eqtz-admin.equiteez.com/equiteez-contract-allowlist-atlasnet.json)."
        )
    return url


async def fetch_allowlist() -> Optional[Dict[str, Set[str]]]:
    url = allowlist_url()
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                raw: Dict[str, Any] = await resp.json(content_type=None)
    except Exception as exc:
        logger.warning("Allowlist fetch failed (%s): %s", url, exc)
        return None

    version = raw.get("schema_version")
    if version != 1:
        logger.warning(
            "Allowlist schema_version=%s; expected 1 — continuing with parsed arrays",
            version,
        )

    out: Dict[str, Set[str]] = {}
    for key in _KEYS:
        items = raw.get(key) or []
        out[key] = {
            addr.strip() for addr in items if isinstance(addr, str) and addr.strip()
        }

    logger.info(
        "Allowlist loaded: orderbooks=%d base_tokens=%d super_admins=%d kyc=%d",
        len(out[ORDERBOOKS]),
        len(out[BASE_TOKENS]),
        len(out[SUPER_ADMINS]),
        len(out[KYC]),
    )
    return out


def allowlist_contains(
    allowlist: Optional[Dict[str, Set[str]]],
    list_key: str,
    address: str,
) -> bool:
    if allowlist is None:
        return False
    return address in (allowlist.get(list_key) or set())
