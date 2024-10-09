# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class TargetEntrypoint(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    freezeMember: bool


class TargetEntrypoint1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    setMember: bool


class TargetEntrypoint2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    unfreezeMember: bool


class TogglePauseEntrypointParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    targetEntrypoint: TargetEntrypoint | TargetEntrypoint1 | TargetEntrypoint2
    field_unit: Dict[str, Any] = Field(..., alias='_unit')
