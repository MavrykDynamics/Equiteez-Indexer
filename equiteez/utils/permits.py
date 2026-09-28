"""
Helpers shared by the permit handlers (`executePermit` / `permitAndExecute`)
and by handlers that need big map removals.

Every permit-enabled contract dispatches a permitted action to the same lambda
as the direct entrypoint, with the verified signer injected as the initiator.
The storage effects are therefore identical to a direct call made by the
signer; the handlers only have to know who the signer is.
"""

import hashlib
from collections.abc import Iterable, Iterator
from typing import Any

import base58
from dipdup.models.tezos import TezosOperationData

# base58check prefixes: public key -> (raw key length, implicit address prefix)
_PUBLIC_KEY_PREFIXES: dict[str, tuple[bytes, int, bytes]] = {
    # ed25519: edpk -> mv1
    "edpk": (bytes([13, 15, 37, 217]), 32, bytes([5, 186, 196])),
    # secp256k1: sppk -> mv2
    "sppk": (bytes([3, 254, 226, 86]), 33, bytes([5, 186, 199])),
    # p256: p2pk -> mv3
    "p2pk": (bytes([3, 178, 139, 127]), 33, bytes([5, 186, 201])),
}


def address_from_public_key(public_key: str) -> str:
    """Implicit account address (mv1/mv2/mv3) owning a base58 public key."""
    try:
        key_prefix, key_length, address_prefix = _PUBLIC_KEY_PREFIXES[public_key[:4]]
    except KeyError as exc:
        raise ValueError(f"Unsupported public key: {public_key}") from exc
    decoded = base58.b58decode_check(public_key)
    if (
        not decoded.startswith(key_prefix)
        or len(decoded) != len(key_prefix) + key_length
    ):
        raise ValueError(f"Malformed public key: {public_key}")
    key_hash = hashlib.blake2b(decoded[len(key_prefix) :], digest_size=20).digest()
    return base58.b58encode_check(address_prefix + key_hash).decode()


def permit_signer(item: Any) -> str:
    """Signer of one executePermit / permitAndExecute item."""
    signer = getattr(item, "signer", None)
    if signer:
        return signer
    return address_from_public_key(item.userPublicKey)


def permit_action(item: Any) -> tuple[str, Any]:
    """(variant name, payload) of a permit item's action, e.g. ("permitTransfer", [...])."""
    fields = item.action.model_dump(exclude_none=False)
    (name,) = fields.keys()
    return name, getattr(item.action, name)


def removed_bigmap_keys(data: TezosOperationData, path: str) -> Iterator[Any]:
    """
    Keys removed from the big map at `path` by this operation.

    Typed storage passed to handlers only carries the keys an operation added or
    updated; removals exist only in the raw diffs.
    """
    for diff in data.diffs:
        if diff.get("path") == path and diff.get("action") == "remove_key":
            yield diff["content"]["key"]


def removed_bigmap_key_set(
    data: TezosOperationData, paths: Iterable[str]
) -> dict[str, list[Any]]:
    return {path: list(removed_bigmap_keys(data, path)) for path in paths}
