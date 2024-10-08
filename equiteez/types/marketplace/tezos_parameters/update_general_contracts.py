# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class UpdateType(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    remove: Dict[str, Any]


class UpdateType1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    update: Dict[str, Any]


class UpdateGeneralContractsParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    generalContractName: str
    generalContractAddress: str
    updateType: UpdateType | UpdateType1
