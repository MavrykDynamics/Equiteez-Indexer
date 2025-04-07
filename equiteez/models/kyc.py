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
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True, null=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    metadata                                = fields.JSONField(null=True)

    class Meta:
        table = 'kyc'

class KycLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.Kyc', related_name='lambdas')

    class Meta:
        table = 'kyc_lambda'

class KycEntrypointStatus(Model, EntrypointStatus):
    contract                                = fields.ForeignKeyField('models.Kyc', related_name='entrypoint_status')

    class Meta:
        table = 'kyc_entrypoint_status'

class KycWhitelisted(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='whitelisted')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_whitelists')

    class Meta:
        table = 'kyc_whitelisted'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycBlacklisted(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='blacklisted')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_blacklists')   

    class Meta:
        table = 'kyc_blacklisted'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycValidInput(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='valid_inputs')
    category                                = fields.IntEnumField(enum_type=ValidInputCategory, index=True)
    valid_inputs                            = fields.ArrayField(element_type="TEXT", default=[])
   
    class Meta:
        table = 'kyc_valid_input'
        indexes = [
            ("kyc_id", "category"),
        ]

class KycRegistrar(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='registrars')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_registrars')   
    name                                    = fields.TextField(index=True, default="")
    kyc_admins                              = fields.ArrayField(element_type="TEXT", default=[])
    member_verified                         = fields.BigIntField(default=0)
    created_at                              = fields.DatetimeField(null=True)
    set_member_is_paused                    = fields.BooleanField(default=False)
    freeze_member_is_paused                 = fields.BooleanField(default=False)
    unfreeze_member_is_paused               = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_registrar'
        indexes = [
            ("kyc_id", "user_id"),
        ]

class KycCountryTransferRule(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='country_transfer_rules')
    country                                 = fields.TextField(index=True)
    whitelist_countries                     = fields.ArrayField(element_type="TEXT", default=[])
    blacklist_countries                     = fields.ArrayField(element_type="TEXT", default=[])
    sending_frozen                          = fields.BooleanField(default=False)
    receiving_frozen                        = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_country_transfer_rule'
        indexes = [
            ("kyc_id", "country"),
        ]

class KycMember(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='members')
    kyc_registrar                           = fields.ForeignKeyField('models.KycRegistrar', related_name='members', null=True)
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='kyc_members', null=True)
    country                                 = fields.TextField(index=True, null=True)
    region                                  = fields.TextField(index=True, null=True)
    investor_type                           = fields.TextField(index=True, null=True)
    expire_at                               = fields.DatetimeField(null=True)
    frozen                                  = fields.BooleanField(default=False, index=True)
   
    class Meta:
        table = 'kyc_member'
        indexes = [
            ("user_id",),
            ("kyc_id", "user_id"),
            ("expire_at", "frozen"),
        ]
