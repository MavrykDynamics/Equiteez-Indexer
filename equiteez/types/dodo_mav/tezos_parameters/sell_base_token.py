# generated by DipDup 8.0.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SellBaseTokenParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    amount: str
    minMaxQuote: str
