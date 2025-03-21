# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, RootModel


class TogglePauseEntrypointParameterItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    entrypoint: str
    pauseBool: bool


class TogglePauseEntrypointParameter(
    RootModel[List[TogglePauseEntrypointParameterItem]]
):
    root: List[TogglePauseEntrypointParameterItem]
