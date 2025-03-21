# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class SetWhitelistAction(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    addToWhitelist: List[str]


class SetWhitelistAction1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    removeFromWhitelist: List[str]


class SetWhitelistParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    setWhitelistAction: SetWhitelistAction | SetWhitelistAction1
    field_unit: Dict[str, Any] = Field(..., alias='_unit')
