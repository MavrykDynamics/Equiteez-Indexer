# generated by DipDup 8.0.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa12Token: str


class Fa2Token(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    tokenContractAddress: str
    tokenId: str


class Token1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa2Token: Fa2Token


class SetCurrencyParameter(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    actionType: str
    name: str
    decimals: str
    token: Token | Token1
