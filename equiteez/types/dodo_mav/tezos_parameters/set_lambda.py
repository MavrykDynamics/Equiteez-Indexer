# generated by DipDup 8.0.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SetLambdaParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: str
    func_bytes: str
