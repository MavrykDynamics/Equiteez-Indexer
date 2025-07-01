from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda, EntrypointStatus

###
# Kyc Enums
###

class ValidInputCategory(IntEnum):
    COUNTRY                                 = 0
    REGION                                  = 1
    INVESTOR_TYPE                           = 2

###
# Kyc Tables
###

class Kyc(Model):
    """
    KYC contract configuration and metadata.
    This table stores the configuration and metadata for KYC (Know Your Customer) contracts
    in Equiteez. KYC contracts handle user verification for regulatory compliance,
    tracking user countries, regions, and investor types.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # KYC contract address
    address                                 = fields.CharField(max_length=36, index=True)

    # Current super admin address
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)

    # Pending super admin address (for transfer)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)

    # Contract metadata
    metadata                                = fields.JSONField(null=True)

    class Meta:
        table = 'kyc'

class KycLambda(Model, ContractLambda):
    """
    Stores lambda functions for a KYC contract.
    This table stores lambda functions associated with KYC contracts.
    """

    # Reference to KYC contract
    contract                                = fields.ForeignKeyField('models.Kyc', related_name='lambdas')

    class Meta:
        table = 'kyc_lambda'

class KycEntrypointStatus(Model, EntrypointStatus):
    """
    Tracks pause status of KYC contract entrypoints.
    This table tracks whether specific entrypoints of KYC contracts are paused
    or active.
    """

    # Reference to KYC contract
    contract                                = fields.ForeignKeyField('models.Kyc', related_name='entrypoint_status')

    class Meta:
        table = 'kyc_entrypoint_status'

class KycWhitelisted(Model):
    """
    Tracks whitelisted users for KYC operations.
    This table maintains a list of users who are whitelisted for KYC operations,
    allowing them to bypass certain verification requirements.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='whitelisted')

    # Whitelisted user
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_whitelists')

    class Meta:
        table = 'kyc_whitelisted'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycBlacklisted(Model):
    """
    Tracks blacklisted users for KYC operations.
    This table maintains a list of users who are blacklisted from KYC operations,
    preventing them from participating in certain activities.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='blacklisted')

    # Blacklisted user
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_blacklists')   

    class Meta:
        table = 'kyc_blacklisted'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycValidInput(Model):
    """
    Stores valid input values for KYC validation.
    This table stores predefined valid values for different KYC input categories,
    such as valid countries, regions, and investor types for validation purposes.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='valid_inputs')

    # Input category (COUNTRY/REGION/INVESTOR_TYPE)
    category                                = fields.IntEnumField(enum_type=ValidInputCategory, index=True)

    # Array of valid input values
    valid_inputs                            = fields.ArrayField(element_type="TEXT", default=[])
   
    class Meta:
        table = 'kyc_valid_input'
        indexes = [
            ("kyc_id", "category"),
        ]

class KycRegistrar(Model):
    """
    Represents KYC registrars who can verify users.
    This table stores information about KYC registrars who are authorized to verify
    users for regulatory compliance. Registrars can set member information, freeze/unfreeze
    accounts, and manage KYC verification processes.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='registrars')

    # Registrar user
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_registrars')

    # Registrar name
    name                                    = fields.TextField(index=True, default="")

    # List of KYC admin addresses
    kyc_admins                              = fields.ArrayField(element_type="TEXT", default=[])

    # Count of verified members
    member_verified                         = fields.BigIntField(default=0)

    # Registrar creation timestamp
    created_at                              = fields.DatetimeField(null=True)

    # Whether set_member entrypoint is paused
    set_member_is_paused                    = fields.BooleanField(default=False)

    # Whether freeze_member entrypoint is paused
    freeze_member_is_paused                 = fields.BooleanField(default=False)

    # Whether unfreeze_member entrypoint is paused
    unfreeze_member_is_paused               = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_registrar'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycCountryTransferRule(Model):
    """
    Defines transfer rules between countries.
    This table stores regulatory transfer rules between countries, including
    whitelisted and blacklisted countries, and whether sending or receiving
    transfers from specific countries is frozen.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='country_transfer_rules')

    # Country code
    country                                 = fields.TextField(index=True)

    # Countries allowed to receive transfers
    whitelist_countries                     = fields.ArrayField(element_type="TEXT", default=[])

    # Countries blocked from transfers
    blacklist_countries                     = fields.ArrayField(element_type="TEXT", default=[])

    # Whether sending from this country is frozen
    sending_frozen                          = fields.BooleanField(default=False)

    # Whether receiving to this country is frozen
    receiving_frozen                        = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_country_transfer_rule'
        indexes = [
            ("kyc_id", "country"),
        ]

class KycMember(Model):
    """
    Represents KYC-verified members/users.
    This table stores KYC verification information for users, including their
    country, region, investor type, and verification status. This information
    is used for regulatory compliance in Equiteez.
    """

    # Primary key identifier
    id                                      = fields.IntField(primary_key=True)

    # Reference to KYC contract
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='members')

    # Registrar who verified the member
    kyc_registrar                           = fields.ForeignKeyField('models.KycRegistrar', related_name='members', null=True)

    # Member user
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_members', null=True)

    # Member's country
    country                                 = fields.TextField(index=True, null=True)

    # Member's region (e.g., asia, north-america)
    region                                  = fields.TextField(index=True, null=True)

    # Type of investor (enterprise, accredited, institution)
    investor_type                           = fields.TextField(index=True, null=True)

    # KYC verification expiry date
    expire_at                               = fields.DatetimeField(null=True)

    # Whether member account is frozen
    frozen                                  = fields.BooleanField(default=False, index=True)
   
    class Meta:
        table = 'kyc_member'
        indexes = [
            ("user_id",),
            ("kyc_id", "user_id"),
            ("expire_at", "frozen"),
        ]
