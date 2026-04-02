from pathlib import Path
from typing import Dict, List, Optional

import yaml


def _contracts_config_path() -> Optional[str]:
    root = Path(__file__).resolve().parents[2]
    yml = root / "dipdup.contracts.yml"
    yaml_path = root / "dipdup.contracts.yaml"
    if yml.exists():
        return str(yml)
    if yaml_path.exists():
        return str(yaml_path)
    return None


def _load_contracts() -> Dict:
    path = _contracts_config_path()
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("contracts", {})


def get_orderbook_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "orderbook" and contract.get("address")
    ]


def get_quote_token_address() -> Optional[str]:
    contracts = _load_contracts()
    for contract in contracts.values():
        if contract.get("typename") == "quote_token":
            return contract.get("address")
    return None


def get_base_token_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "base_token" and contract.get("address")
    ]


def get_liquidity_pool_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "liquidity_pool" and contract.get("address")
    ]


def get_superadmin_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "superadmin" and contract.get("address")
    ]


def get_maven_lending_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "maven_lending" and contract.get("address")
    ]
