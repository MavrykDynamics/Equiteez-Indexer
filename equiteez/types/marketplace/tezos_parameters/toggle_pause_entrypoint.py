# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class TargetEntrypoint(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    acceptOffer: bool


class TargetEntrypoint1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    createListing: bool


class TargetEntrypoint2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    editListing: bool


class TargetEntrypoint3(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    offer: bool


class TargetEntrypoint4(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    purchase: bool


class TargetEntrypoint5(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    removeListing: bool


class TargetEntrypoint6(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    removeOffer: bool


class TargetEntrypoint7(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    setCurrency: bool


class TogglePauseEntrypointParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    targetEntrypoint: (
        TargetEntrypoint
        | TargetEntrypoint1
        | TargetEntrypoint2
        | TargetEntrypoint3
        | TargetEntrypoint4
        | TargetEntrypoint5
        | TargetEntrypoint6
        | TargetEntrypoint7
    )
    empty: Dict[str, Any]
