from dipdup.models import Model, fields
from equiteez.models.shared import ContractLambda

###
# Kyc Tables
###

class Kyc(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    super_admin                             = fields.CharField(max_length=36, index=True)
    new_super_admin                         = fields.CharField(max_length=36, index=True, null=True)
    metadata                                = fields.JSONField(null=True)
    set_member_is_paused                    = fields.BooleanField(default=False)
    freeze_member_is_paused                 = fields.BooleanField(default=False)
    unfreeze_member_is_paused               = fields.BooleanField(default=False)

    class Meta:
        table = 'kyc'

class KycLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.Kyc', related_name='lambdas')

    class Meta:
        table = 'kyc_lambda'

class KycWhitelisted(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='whitelisted')
    address                                 = fields.CharField(max_length=36, index=True)
   
    class Meta:
        table = 'kyc_whitelisted'

class KycBlacklisted(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='blacklisted')
    address                                 = fields.CharField(max_length=36, index=True)
   
    class Meta:
        table = 'kyc_blacklisted'

class KycValidInput(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='valid_inputs')
    category                                = fields.TextField(index=True)
    valid_inputs                            = fields.ArrayField()
   
    class Meta:
        table = 'kyc_valid_input'

class KycRegistrar(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='registrars')
    address                                 = fields.CharField(max_length=36, index=True)
    name                                    = fields.TextField(index=True)
    kyc_admins                              = fields.ArrayField()
    member_verified                         = fields.BigIntField(default=0)
    created_at                              = fields.TimeField(null=True)
    set_member_is_paused                    = fields.BooleanField(default=False)
    freeze_member_is_paused                 = fields.BooleanField(default=False)
    unfreeze_member_is_paused               = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_registrar'

class KycCountryTransferRule(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='country_transfer_rules')
    rule_name                               = fields.TextField(index=True)
    whitelist_countries                     = fields.ArrayField()
    blacklist_countries                     = fields.ArrayField()
    sending_frozen                          = fields.BooleanField(default=False)
    receiving_frozen                        = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_country_transfer_rule'

class KycMember(Model):
    id                                      = fields.IntField(primary_key=True)
    kyc                                     = fields.ForeignKeyField('models.Kyc', related_name='members')
    kyc_registrar                           = fields.ForeignKeyField('models.KycRegistrar', related_name='members')
    address                                 = fields.CharField(max_length=36, index=True)
    country                                 = fields.TextField(index=True, null=True)
    region                                  = fields.TextField(index=True, null=True)
    investor_type                           = fields.TextField(index=True, null=True)
    expire_at                               = fields.TimeField(null=True)
    frozen                                  = fields.BooleanField(default=False)
   
    class Meta:
        table = 'kyc_member'
