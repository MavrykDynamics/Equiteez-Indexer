# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class Currency(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa12: str


class Fa2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    tokenContractAddress: str
    tokenId: str


class Currency1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa2: Fa2


class Currency2(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    tez: Dict[str, Any]


class OfferParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    listingId: str
    price: str
    amount: str
    expiryTime: str | None = None
    currency: Currency | Currency1 | Currency2
