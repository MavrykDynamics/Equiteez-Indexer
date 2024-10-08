# generated by DipDup 8.0.0

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class Config(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    minOfferAmount: str
    standardUnit: str
    royalty: str
    marketplaceFee: str


class BreakGlassConfig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    createListingIsPaused: bool
    editListingIsPaused: bool
    removeListingIsPaused: bool
    purchaseIsPaused: bool
    offerIsPaused: bool
    acceptOfferIsPaused: bool
    removeOfferIsPaused: bool
    setCurrencyIsPaused: bool


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


class ListingLedger(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    initiator: str
    status: str
    token: Token | Token1
    amount: str
    pricePerUnit: str
    currency: Currency | Currency1 | Currency2
    quickBuyPrice: str | None = None
    expiryTime: str | None = None


class Currency3(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa12: str


class Currency4(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    fa2: Fa2


class Currency5(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    tez: Dict[str, Any]


class OfferLedger(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    initiator: str
    status: str
    listingId: str
    price: str
    amount: str
    currency: Currency3 | Currency4 | Currency5
    expiryTime: str | None = None


class CurrencyLedger(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    tokenType: str
    tokenIds: List[str]


class MarketplaceStorage(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    superAdmin: str
    newSuperAdmin: str | None = None
    admins: List[str]
    metadata: Dict[str, str]
    config: Config
    breakGlassConfig: BreakGlassConfig
    whitelistContracts: Dict[str, str]
    generalContracts: Dict[str, str]
    nextListingId: str
    nextOfferId: str
    listingLedger: Dict[str, ListingLedger]
    offerLedger: Dict[str, OfferLedger]
    currencyLedger: Dict[str, CurrencyLedger]
    lambdaLedger: Dict[str, str]
