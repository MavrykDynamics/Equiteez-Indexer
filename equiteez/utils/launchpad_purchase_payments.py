"""Attribute confirmed payment operations to launchpad purchases.

The launchpad emits [issuance?, net payment, discounted fee?] per purchase.
Permit helpers concatenate these groups in action order. MvKT IDs reflect
execution order; nonces reflect creation order and MUST NOT be sorted here.
We require a unique complete match of every launchpad-emitted transaction.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PurchaseTerms:
    buyer: str
    amount: int
    price: int
    maximum: int
    fee_bps: int
    currency: str
    token_address: str | None
    token_id: int
    distribution: str
    issuance: str
    rwa_address: str
    rwa_id: int


def terms_for(storage, purchase, buyer):
    launch = storage.launchLedger[purchase.launchName]
    payment = launch.saleOptions[purchase.saleOption].payments[purchase.payment]
    currency = payment.currency
    if getattr(currency, "fa2", None) is not None:
        kind, address, token_id = (
            "fa2",
            currency.fa2.tokenContractAddress,
            int(currency.fa2.tokenId),
        )
    elif getattr(currency, "fa12", None):
        kind, address, token_id = "fa12", currency.fa12, 0
    elif getattr(currency, "mav", None) is not None:
        kind, address, token_id = "mav", None, 0
    else:
        raise ValueError("unknown payment currency")
    terms = PurchaseTerms(
        buyer=buyer,
        amount=int(purchase.amount),
        price=int(payment.price),
        maximum=int(purchase.maxTotalPayment),
        fee_bps=int(launch.purchaseFeePercent),
        currency=kind,
        token_address=address,
        token_id=token_id,
        distribution=launch.tokenDistributionType,
        issuance=launch.tokenIssuanceType,
        rwa_address=launch.tokenContractAddress,
        rwa_id=int(launch.tokenId),
    )
    if min(terms.amount, terms.price, terms.maximum, terms.token_id, terms.rwa_id) < 0:
        raise ValueError("negative natural")
    if not 0 <= terms.fee_bps <= 10000:
        raise ValueError("invalid purchase fee")
    if terms.distribution not in ("AUTO", "MANUAL"):
        raise ValueError("unknown distribution mode")
    return terms


def _nat(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("invalid natural")
    text = str(value)
    if not text.isascii() or not text.isdecimal():
        raise ValueError("invalid natural")
    return int(text)


def _address(operation, field):
    return (operation.get(field) or {}).get("address")


def _transfer_amount(op, currency, token, token_id, sender, recipient):
    if not recipient:
        return None
    parameter = op.get("parameter") or {}
    if currency == "mav":
        if (
            _address(op, "target") == recipient
            and parameter.get("entrypoint", "default") == "default"
        ):
            return _nat(op["amount"])
        return None
    if (
        _address(op, "target") != token
        or _nat(op.get("amount", 0)) != 0
        or parameter.get("entrypoint") != "transfer"
    ):
        return None
    if not sender:
        return None
    value = parameter.get("value")
    if currency == "fa12":
        if (
            isinstance(value, dict)
            and value.get("from") == sender
            and value.get("to") == recipient
        ):
            return _nat(value["value"])
    elif currency == "fa2" and isinstance(value, list) and len(value) == 1:
        item = value[0]
        txs = item.get("txs", [])
        if item.get("from_") == sender and len(txs) == 1:
            tx = txs[0]
            if tx.get("to_") == recipient and _nat(tx["token_id"]) == token_id:
                return _nat(tx["amount"])
    return None


def _issuance_matches(op, terms, treasury):
    if terms.issuance == "TRANSFER":
        return (
            _transfer_amount(
                op,
                "fa2",
                terms.rwa_address,
                terms.rwa_id,
                treasury.get("launchTreasury"),
                terms.buyer,
            )
            == terms.amount
        )
    parameter = op.get("parameter") or {}
    if (
        terms.issuance == "MINT"
        and _address(op, "target") == terms.rwa_address
        and _nat(op.get("amount", 0)) == 0
        and parameter.get("entrypoint") == "mint"
    ):
        value = parameter.get("value")
        if isinstance(value, list) and len(value) == 1:
            item = value[0]
            return (
                item.get("owner") == terms.buyer
                and _nat(item["token_id"]) == terms.rwa_id
                and _nat(item["amount"]) == terms.amount
            )
    return False


def payment_totals(data, receipt, terms, treasury):
    """Return exact totals, or (None, reason) for unsupported/ambiguous effects.

    A missing/mismatched parent is a transient datasource failure: raise instead
    of permanently writing unknown money. All other mismatches fail closed.
    """
    parents = [r for r in receipt if r.get("id") == data.id]
    if len(parents) != 1:
        raise RuntimeError("Purchase receipt is missing its indexed transaction")
    parent = parents[0]
    if any(
        parent.get(k) != value
        for k, value in (
            ("hash", data.hash),
            ("counter", data.counter),
            ("nonce", data.nonce),
            ("level", data.level),
            ("status", "applied"),
        )
    ) or (data.block and parent.get("block") != data.block):
        raise RuntimeError(
            "Purchase receipt does not match the indexed block/transaction"
        )
    if (
        _address(parent, "target") != data.target_address
        or _address(parent, "sender") != data.sender_address
    ):
        raise RuntimeError("Purchase receipt identities do not match")

    group = [
        r
        for r in receipt
        if r.get("hash") == data.hash and r.get("counter") == data.counter
    ]
    if sum(_address(r, "target") == data.target_address for r in group) != 1:
        return None, "nested_launchpad_calls"
    if any(
        r.get("status") != "applied"
        or r.get("level") != data.level
        or (data.block and r.get("block") != data.block)
        for r in group
    ):
        raise RuntimeError("Incomplete or inconsistent purchase receipt")
    operations = sorted(
        (r for r in group if _address(r, "sender") == data.target_address),
        key=lambda r: r["id"],
    )
    if any(r.get("nonce") is None or r["id"] <= data.id for r in operations):
        return None, "invalid_internal_coordinates"
    if len({r["id"] for r in operations}) != len(operations) or len(
        {r["nonce"] for r in operations}
    ) != len(operations):
        return None, "duplicate_internal_operation"
    if not treasury.get("assetTreasury") or not treasury.get("feeTreasury"):
        return None, "unknown_treasury"
    if not terms or len(operations) > 4096:
        return None, "unsupported_receipt_size"

    # Dynamic programming keeps at most two distinct histories for each offset.
    # An optional fee must never consume the next purchase's net transfer.
    states = {0: [()]}
    try:
        for term in terms:
            next_states = {}
            if term.distribution not in ("AUTO", "MANUAL"):
                return None, "unknown_distribution"
            subtotal = (term.price * term.amount + 999999) // 1000000
            full_fee = subtotal * term.fee_bps // 10000
            net = subtotal - full_fee
            for offset, histories in states.items():
                pos = offset
                if term.distribution == "AUTO":
                    if pos >= len(operations) or not _issuance_matches(
                        operations[pos], term, treasury
                    ):
                        continue
                    pos += 1
                if (
                    pos >= len(operations)
                    or _transfer_amount(
                        operations[pos],
                        term.currency,
                        term.token_address,
                        term.token_id,
                        term.buyer,
                        treasury["assetTreasury"],
                    )
                    != net
                ):
                    continue
                pos += 1
                choices = [(pos, net)]
                if pos < len(operations):
                    fee = _transfer_amount(
                        operations[pos],
                        term.currency,
                        term.token_address,
                        term.token_id,
                        term.buyer,
                        treasury["feeTreasury"],
                    )
                    if fee is not None and 0 < fee <= full_fee:
                        choices.append((pos + 1, net + fee))
                for end, total in choices:
                    if total > term.maximum:
                        continue
                    bucket = next_states.setdefault(end, [])
                    for history in histories:
                        candidate = (*history, total)
                        if candidate not in bucket and len(bucket) < 2:
                            bucket.append(candidate)
            states = next_states
        results = states.get(len(operations), [])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None, "unsupported_payment_shape"
    if len(results) != 1:
        return None, "ambiguous_or_unmatched_payments"
    totals = results[0]
    if any(t.currency == "mav" for t in terms):
        if len(terms) != 1 or data.entrypoint != "purchase" or data.amount != totals[0]:
            return None, "unsupported_native_payment"
    elif data.amount != 0:
        return None, "unexpected_attached_mav"
    return totals, None


_last_receipt = None


async def fetch_receipt(ctx, data):
    """One cached group, keyed by datasource and block to remain reorg-safe."""
    global _last_receipt
    config = ctx.handler_config.parent
    datasource = ctx.get_tezos_tzkt_datasource(config.datasources[0].name)
    key = (id(datasource), data.block, data.level, data.hash)
    if data.block and _last_receipt and _last_receipt[0] == key:
        cached = _last_receipt[1]
        if any(r.get("id") == data.id for r in cached):
            return cached
    receipt = await datasource.request("get", f"v1/operations/transactions/{data.hash}")
    if not isinstance(receipt, list) or not any(
        r.get("id") == data.id for r in receipt
    ):
        raise RuntimeError("Purchase receipt is not available yet")
    parent = next(r for r in receipt if r.get("id") == data.id)
    if (
        parent.get("hash") != data.hash
        or parent.get("counter") != data.counter
        or parent.get("nonce") != data.nonce
        or parent.get("level") != data.level
        or parent.get("status") != "applied"
        or _address(parent, "target") != data.target_address
        or _address(parent, "sender") != data.sender_address
    ):
        raise RuntimeError("Purchase receipt does not match its indexed transaction")
    # DipDup's historical REST projection omits the block hash. In that path
    # also compare the operation inputs/diffs; never cache an unpinned group.
    if not data.block and (
        (parent.get("parameter") or {}).get("value") != data.parameter_json
        or tuple(parent.get("diffs") or ()) != data.diffs
    ):
        raise RuntimeError("Historical purchase receipt differs from indexed data")
    if any(
        r.get("hash") != data.hash
        or r.get("level") != data.level
        or r.get("status") != "applied"
        or (data.block and r.get("block") != data.block)
        for r in receipt
    ):
        raise RuntimeError("Purchase receipt is inconsistent with the indexed block")
    if data.has_internals and not any(
        r.get("counter") == data.counter
        and r.get("nonce") is not None
        and _address(r, "sender") == data.target_address
        for r in receipt
    ):
        raise RuntimeError("Purchase receipt is missing internal operations")
    if data.block:
        _last_receipt = (key, receipt)
    return receipt


async def resolve_totals(ctx, transaction, purchases, treasury):
    try:
        terms = [
            terms_for(transaction.storage, purchase, buyer)
            for purchase, buyer in purchases
        ]
    except (KeyError, AttributeError, TypeError, ValueError):
        ctx.logger.warning(
            "launch purchase payment unavailable: unsupported_purchase_terms"
        )
        return [None] * len(purchases)
    receipt = await fetch_receipt(ctx, transaction.data)
    totals, reason = payment_totals(transaction.data, receipt, terms, treasury)
    if reason:
        ctx.logger.warning(
            "launch purchase payment unavailable: %s (operation_id=%s)",
            reason,
            transaction.data.id,
        )
        return [None] * len(purchases)
    return totals
