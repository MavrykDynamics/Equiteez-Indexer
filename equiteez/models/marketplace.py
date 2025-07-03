from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda

###
# Marketplace Enums
###


class ListingStatus(IntEnum):
    CLOSED = 0
    ACTIVE = 1


class OfferStatus(IntEnum):
    CLOSED = 0
    OPEN = 1
    ACCEPTED = 2


###
# Marketplace Tables
###


class Marketplace(Model):
    """
    Marketplace contract configuration and state.
    This table stores the configuration and current state of marketplace contracts
    for RWA trading. Marketplaces manage listings, offers,
    fees, and trading operations for RWA tokens with regulatory compliance.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Marketplace contract address
    address = fields.CharField(max_length=36, index=True)

    # Current super admin address
    super_admin = fields.CharField(max_length=36, index=True, null=True)

    # Pending super admin address
    new_super_admin = fields.CharField(max_length=36, index=True, null=True)

    # List of admin addresses
    admins = fields.ArrayField(element_type="TEXT", default=[])

    # Contract metadata
    metadata = fields.JSONField(null=True)

    # Minimum offer amount
    min_offer_amount = fields.BigIntField(default=0)

    # Standard unit for pricing
    standard_unit = fields.BigIntField(default=0)

    # Royalty percentage
    royalty = fields.BigIntField(default=0)

    # Marketplace fee percentage
    marketplace_fee = fields.BigIntField(default=0)

    # Whether create_listing is paused
    create_listing_is_paused = fields.BooleanField(default=False)

    # Whether edit_listing is paused
    edit_listing_is_paused = fields.BooleanField(default=False)

    # Whether remove_listing is paused
    remove_listing_is_paused = fields.BooleanField(default=False)

    # Whether purchase is paused
    purchase_is_paused = fields.BooleanField(default=False)

    # Whether offer creation is paused
    offer_is_paused = fields.BooleanField(default=False)

    # Whether offer acceptance is paused
    accept_offer_is_paused = fields.BooleanField(default=False)

    # Whether offer removal is paused
    remove_offer_is_paused = fields.BooleanField(default=False)

    # Whether currency setting is paused
    set_currency_is_paused = fields.BooleanField(default=False)

    # Next available listing ID
    next_listing_id = fields.BigIntField(default=0)

    # Next available offer ID
    next_offer_id = fields.BigIntField(default=0)

    class Meta:
        table = "marketplace"


class MarketplaceLambda(Model, ContractLambda):
    """
    Stores lambda functions for a marketplace contract.
    This table stores lambda functions associated with marketplace contracts.
    """

    # Reference to marketplace contract
    contract = fields.ForeignKeyField("models.Marketplace", related_name="lambdas")

    class Meta:
        table = "marketplace_lambda"


class MarketplaceWhitelistContract(Model):
    """
    Tracks whitelisted contracts for marketplace operations.
    This table stores contracts that are whitelisted for marketplace operations,
    allowing them to participate in trading activities.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to marketplace contract
    marketplace = fields.ForeignKeyField(
        "models.Marketplace", related_name="whitelist_contracts"
    )

    # Address of the whitelisted contract
    address = fields.CharField(max_length=36, index=True)

    class Meta:
        table = "marketplace_whitelist_contract"
        indexes = [
            ("marketplace_id", "address"),
        ]


class MarketplaceGeneralContract(Model):
    """
    Tracks general contracts associated with marketplaces.
    This table stores general contracts that are associated with marketplace
    operations, such as token contracts or other supporting contracts.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to marketplace contract
    marketplace = fields.ForeignKeyField(
        "models.Marketplace", related_name="general_contracts"
    )

    # Address of the general contract
    address = fields.CharField(max_length=36, index=True)

    class Meta:
        table = "marketplace_general_contract"
        indexes = [
            ("marketplace_id", "address"),
        ]


class MarketplaceCurrency(Model):
    """
    Defines currencies accepted by marketplaces.
    This table stores the currencies that are accepted for trading in marketplaces,
    including both native tokens and external tokens.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to marketplace contract
    marketplace = fields.ForeignKeyField(
        "models.Marketplace", related_name="currencies"
    )

    # Token associated with this currency
    token = fields.ForeignKeyField(
        "models.Token", related_name="marketplace_currencies", null=True
    )

    class Meta:
        table = "marketplace_currency"
        indexes = [
            ("marketplace_id", "token_id"),
        ]


class MarketplaceListing(Model):
    """
    Stores marketplace listings for tokens.
    This table stores all listings created in marketplaces for RWA token trading.
    Each listing represents an offer to sell a specific amount of tokens at a
    given price, with optional quick buy pricing and expiry times.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to marketplace contract
    marketplace = fields.ForeignKeyField("models.Marketplace", related_name="listings")

    # User who created the listing
    initiator = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="marketplace_listings"
    )

    # Token being listed
    token = fields.ForeignKeyField(
        "models.Token", related_name="marketplace_listing_tokens"
    )

    # Listing currency
    currency = fields.ForeignKeyField(
        "models.MarketplaceCurrency", related_name="listings"
    )

    # Unique listing identifier
    listing_id = fields.BigIntField(default=0, index=True)

    # Listing status (CLOSED/ACTIVE)
    status = fields.IntEnumField(enum_type=ListingStatus, index=True)

    # Token amount listed
    amount = fields.FloatField(default=0.0)

    # Price per token unit
    price_per_unit = fields.BigIntField(default=0, index=True)

    # Quick buy price (if available)
    quick_buy_price = fields.BigIntField(null=True)

    # Listing expiry timestamp
    expiry_time = fields.DatetimeField(null=True, index=True)

    class Meta:
        table = "marketplace_listing"
        indexes = [
            ("marketplace_id", "listing_id"),
            ("token_id", "status"),
            ("initiator_id", "status"),
            ("status", "price_per_unit", "expiry_time"),
        ]


class MarketplaceOffer(Model):
    """
    Stores offers made on marketplace listings.
    This table stores all offers made by users on marketplace listings for RWA tokens.
    Each offer represents a bid to purchase tokens at a specific price, with
    status tracking and expiry times.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to marketplace contract
    marketplace = fields.ForeignKeyField("models.Marketplace", related_name="offers")

    # Reference to the listing
    listing = fields.ForeignKeyField("models.MarketplaceListing", related_name="offers")

    # User who made the offer
    initiator = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="marketplace_offers"
    )

    # Offer currency
    currency = fields.ForeignKeyField(
        "models.MarketplaceCurrency", related_name="offers"
    )

    # Unique offer identifier
    offer_id = fields.BigIntField(default=0, index=True)

    # Offer status (CLOSED/OPEN/ACCEPTED)
    status = fields.IntEnumField(enum_type=OfferStatus, index=True)

    # Token amount offered
    amount = fields.FloatField(default=0.0)

    # Offer price
    price = fields.BigIntField(default=0, index=True)

    # Offer expiry timestamp
    expiry_time = fields.DatetimeField(null=True, index=True)

    class Meta:
        table = "marketplace_offer"
        indexes = [
            ("marketplace_id", "offer_id"),
            ("listing_id", "status"),
            ("initiator_id", "status"),
            ("status", "price", "expiry_time"),
        ]
