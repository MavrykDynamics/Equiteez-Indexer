from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda

###
# Marketplace Enums
###

class ListingStatus(IntEnum):
    CLOSED                                  = 0
    ACTIVE                                  = 1

class OfferStatus(IntEnum):
    CLOSED                                  = 0
    OPEN                                    = 1
    ACCEPTED                                = 2

###
# Marketplace Tables
###

class Marketplace(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    admins                                  = fields.ArrayField(element_type="TEXT", default=[])
    metadata                                = fields.JSONField(null=True)
    min_offer_amount                        = fields.BigIntField(default=0)
    standard_unit                           = fields.BigIntField(default=0)
    royalty                                 = fields.BigIntField(default=0)
    marketplace_fee                         = fields.BigIntField(default=0)
    create_listing_is_paused                = fields.BooleanField(default=False)
    edit_listing_is_paused                  = fields.BooleanField(default=False)
    remove_listing_is_paused                = fields.BooleanField(default=False)
    purchase_is_paused                      = fields.BooleanField(default=False)
    offer_is_paused                         = fields.BooleanField(default=False)
    accept_offer_is_paused                  = fields.BooleanField(default=False)
    remove_offer_is_paused                  = fields.BooleanField(default=False)
    set_currency_is_paused                  = fields.BooleanField(default=False)
    next_listing_id                         = fields.BigIntField(default=0)
    next_offer_id                           = fields.BigIntField(default=0)

    class Meta:
        table = 'marketplace'

class MarketplaceLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.Marketplace', related_name='lambdas')

    class Meta:
        table = 'marketplace_lambda'

class MarketplaceWhitelistContract(Model):
    id                                      = fields.IntField(primary_key=True)
    marketplace                             = fields.ForeignKeyField('models.Marketplace', related_name='whitelist_contracts')
    address                                 = fields.CharField(max_length=36, index=True)

    class Meta:
        table = 'marketplace_whitelist_contract'

class MarketplaceGeneralContract(Model):
    id                                      = fields.IntField(primary_key=True)
    marketplace                             = fields.ForeignKeyField('models.Marketplace', related_name='general_contracts')
    address                                 = fields.CharField(max_length=36, index=True)

    class Meta:
        table = 'marketplace_general_contract'

class MarketplaceCurrency(Model):
    id                                      = fields.IntField(primary_key=True)
    marketplace                             = fields.ForeignKeyField('models.Marketplace', related_name='currencies')
    token                                   = fields.ForeignKeyField('models.Token', related_name='marketplace_currencies', null=True)

    class Meta:
        table = 'marketplace_currency'

class MarketplaceListing(Model):
    id                                      = fields.IntField(primary_key=True)
    marketplace                             = fields.ForeignKeyField('models.Marketplace', related_name='listings')
    initiator                               = fields.ForeignKeyField('models.EquiteezUser', related_name='marketplace_listings')
    token                                   = fields.ForeignKeyField('models.Token', related_name='marketplace_listing_tokens')
    currency                                = fields.ForeignKeyField('models.MarketplaceCurrency', related_name='listings')
    listing_id                              = fields.BigIntField(default=0, index=True)
    status                                  = fields.IntEnumField(enum_type=ListingStatus, index=True)
    amount                                  = fields.FloatField(default=0.0)
    price_per_unit                          = fields.BigIntField(default=0, index=True)
    quick_buy_price                         = fields.BigIntField(null=True)
    expiry_time                             = fields.DatetimeField(null=True, index=True)

    class Meta:
        table = 'marketplace_listing'

class MarketplaceOffer(Model):
    id                                      = fields.IntField(primary_key=True)
    marketplace                             = fields.ForeignKeyField('models.Marketplace', related_name='offers')
    listing                                 = fields.ForeignKeyField('models.MarketplaceListing', related_name='offers')
    initiator                               = fields.ForeignKeyField('models.EquiteezUser', related_name='marketplace_offers')
    currency                                = fields.ForeignKeyField('models.MarketplaceCurrency', related_name='offers')
    offer_id                                = fields.BigIntField(default=0, index=True)
    status                                  = fields.IntEnumField(enum_type=OfferStatus, index=True)
    amount                                  = fields.FloatField(default=0.0)
    price                                   = fields.BigIntField(default=0, index=True)
    expiry_time                             = fields.DatetimeField(null=True, index=True)

    class Meta:
        table = 'marketplace_offer'
