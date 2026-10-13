from dipdup.models.tezos import TezosOperationData

from equiteez.models import RwaTokenBalance, RwaTokenSupply


def nat(value: object) -> int:
    number = int(str(value))
    if number < 0 or str(number) != str(value) or number >= 10**76:
        raise ValueError(f"Invalid RWA natural number: {value!r}")
    return number


async def sync_token_supply(operation: TezosOperationData) -> None:
    """Mirror absolute big-map updates inside the caller's DipDup transaction.

    Typed storage contains only changed keys and loses remove_key entries.
    Always consume raw diffs, including internal operations. Assigning balances
    (instead of adding transfer amounts) also makes replay idempotent.
    """
    if operation.status != "applied":
        return
    address = operation.originated_contract_address or operation.target_address
    if not address or not isinstance(operation.storage, dict):
        raise ValueError("RWA operation must include its contract and storage")

    # Some deployments originate token_metadata while token_ids is still empty.
    token_ids = set(operation.storage["token_ids"])
    for diff in operation.diffs:
        if diff.get("action") not in ("add_key", "update_key", "remove_key"):
            continue
        if diff.get("path") in ("total_supply", "token_metadata"):
            token_ids.add(str(diff["content"]["key"]))
        elif diff.get("path") == "ledger":
            token_ids.add(str(diff["content"]["key"]["token_id"]))
    tokens = {}
    for token_id in token_ids:
        token_id = str(nat(token_id))
        token, _ = await RwaTokenSupply.get_or_create(
            id=f"{address}:{token_id}",
            defaults={"contract": address, "token_id": token_id},
        )
        tokens[token_id] = token

    if operation.storage["isKilled"]:
        for token in await RwaTokenSupply.filter(contract=address):
            token.total_supply_raw = 0
            await token.save()
            await RwaTokenBalance.filter(token=token).delete()
        return

    for diff in operation.diffs:
        path = diff.get("path")
        if path not in ("ledger", "total_supply"):
            continue
        action = diff["action"]
        if action == "allocate":
            continue
        if action not in ("add_key", "update_key", "remove_key"):
            # Copy/removal of an entire live ledger requires an explicit rebuild;
            # never silently publish partial balances. kill is handled above.
            raise ValueError(f"Unsupported RWA big-map action: {path}/{action}")
        content = diff["content"]
        key = content["key"]
        token_id = str(nat(key["token_id"] if path == "ledger" else key))
        token = tokens[token_id]
        amount = 0 if action == "remove_key" else nat(content["value"])
        if path == "total_supply":
            token.total_supply_raw = amount
            await token.save()
        elif amount:
            await RwaTokenBalance.update_or_create(
                token=token, holder=key["owner"], defaults={"balance_raw": amount}
            )
        else:
            await RwaTokenBalance.filter(token=token, holder=key["owner"]).delete()
