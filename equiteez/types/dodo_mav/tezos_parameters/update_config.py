# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, RootModel


class UpdateConfigParameterItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    configName: str
    newValue: str


class UpdateConfigParameter(RootModel[List[UpdateConfigParameterItem]]):
    root: List[UpdateConfigParameterItem]
