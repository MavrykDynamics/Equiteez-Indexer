# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, RootModel


class CancelOrdersParameterItem(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    orderId: str
    orderType: str


class CancelOrdersParameter(RootModel[List[CancelOrdersParameterItem]]):
    root: List[CancelOrdersParameterItem]
