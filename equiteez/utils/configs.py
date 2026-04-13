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


def get_quote_token_address() -> Optional[str]:
    contracts = _load_contracts()
    entry = contracts.get("quote_token")
    if entry and entry.get("address"):
        return str(entry["address"])
    return None


def get_liquidity_pool_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "liquidity_pool" and contract.get("address")
    ]


def get_maven_lending_addresses() -> List[str]:
    contracts = _load_contracts()
    return [
        contract["address"]
        for contract in contracts.values()
        if contract.get("typename") == "maven_lending" and contract.get("address")
    ]
