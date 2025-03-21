# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class AddMemberItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    memberAddress: str
    country: str
    region: str
    investorType: str


class SetMemberAction(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    addMember: List[AddMemberItem]


class SetMemberAction1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    removeMember: List[str]


class UpdateMemberItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    memberAddress: str
    country: str | None = None
    region: str | None = None
    investorType: str | None = None
    expireAt: str | None = None


class SetMemberAction2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    updateMember: List[UpdateMemberItem]


class SetMemberParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    setMemberAction: SetMemberAction | SetMemberAction1 | SetMemberAction2
    field_unit: Dict[str, Any] = Field(..., alias='_unit')
