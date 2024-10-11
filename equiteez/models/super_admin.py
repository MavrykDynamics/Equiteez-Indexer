from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda, EntrypointStatus

###
# SuperAdmin Enums
###

class ActionStatus(IntEnum):
    FLUSHED                                 = 0
    EXECUTED                                = 1
    PENDING                                 = 2

###
# SuperAdmin Tables
###

class SuperAdmin(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    metadata                                = fields.JSONField(null=True)
    signatory_size                          = fields.BigIntField(default=0)
    action_counter                          = fields.BigIntField(default=0)
    threshold                               = fields.BigIntField(default=0)
    action_expiry_in_seconds                = fields.BigIntField(default=0)

    class Meta:
        table = 'super_admin'

class SuperAdminLambda(Model, ContractLambda):
    contract                                = fields.ForeignKeyField('models.SuperAdmin', related_name='lambdas')

    class Meta:
        table = 'super_admin_lambda'

class SuperAdminSignatory(Model):
    id                                      = fields.IntField(primary_key=True)
    super_admin                             = fields.ForeignKeyField('models.SuperAdmin', related_name='signatories')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='super_admin_signatories')

    class Meta:
        table = 'super_admin_signatory'

class SuperAdminGeneralAdmin(Model):
    id                                      = fields.IntField(primary_key=True)
    super_admin                             = fields.ForeignKeyField('models.SuperAdmin', related_name='general_admins')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='super_admin_general_admins')

    class Meta:
        table = 'super_admin_general_admin'

class SuperAdminContractAdmin(Model):
    id                                      = fields.IntField(primary_key=True)
    super_admin                             = fields.ForeignKeyField('models.SuperAdmin', related_name='contract_admins')
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='super_admin_contract_admins')
    contract_address                        = fields.CharField(max_length=36, index=True)

    class Meta:
        table = 'super_admin_contract_admin'

class SuperAdminSignatoryAction(Model):
    id                                      = fields.IntField(primary_key=True)
    super_admin                             = fields.ForeignKeyField('models.SuperAdmin', related_name='signatory_actions')
    initiator                               = fields.ForeignKeyField('models.SuperAdminSignatory', related_name='signatory_actions')
    action_id                               = fields.BigIntField(default=0)
    action_type                             = fields.TextField(default="")
    executed                                = fields.BooleanField(default=False)
    status                                  = fields.IntEnumField(enum_type=ActionStatus, index=True, default=ActionStatus.PENDING)
    signers_count                           = fields.BigIntField(default=0)
    start_datetime                          = fields.DatetimeField(null=True)
    start_level                             = fields.BigIntField(default=0)
    executed_datetime                       = fields.DatetimeField(null=True)
    executed_level                          = fields.BigIntField(null=True)
    expiration_datetime                     = fields.DatetimeField(null=True)

    class Meta:
        table = 'super_admin_signatory_action'

class SuperAdminSignatoryActionData(Model):
    id                                      = fields.IntField(primary_key=True)
    action                                  = fields.ForeignKeyField('models.SuperAdminSignatoryAction', related_name='data')
    name                                    = fields.TextField()
    bytes                                   = fields.TextField()

    class Meta:
        table = 'super_admin_signatory_action_data'

class SuperAdminSignature(Model):
    id                                      = fields.IntField(primary_key=True)
    super_admin                             = fields.ForeignKeyField('models.SuperAdmin', related_name='signatures')
    signatory                               = fields.ForeignKeyField('models.SuperAdminSignatory', related_name='signatures')
    action                                  = fields.ForeignKeyField('models.SuperAdminSignatoryAction', related_name='signatures')

    class Meta:
        table = 'super_admin_signature'
