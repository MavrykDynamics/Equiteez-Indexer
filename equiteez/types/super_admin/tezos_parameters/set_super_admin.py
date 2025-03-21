# generated by DipDup 8.0.0

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class SetSuperAdminParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    superAdminAddress: str
    contractAddressList: List[str]
