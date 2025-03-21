# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class SetContractAdminParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    adminAddress: str
    contractAddressList: List[str]
