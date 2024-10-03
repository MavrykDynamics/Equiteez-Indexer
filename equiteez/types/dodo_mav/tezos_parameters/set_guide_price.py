# generated by DipDup 8.0.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SetGuidePriceParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    configType: str
    natOption: str | None = None
    stringOption: str | None = None
