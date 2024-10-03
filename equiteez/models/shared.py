from dipdup.models import Model, fields
from enum import IntEnum

###
# Shared Enums
###

class TokenType(IntEnum):
    FA12                                    = 0
    FA2                                     = 1
    MAV                                     = 2

###
# Shared Tables
###

class Token(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)
    token_id                                = fields.SmallIntField(default=0)
    metadata                                = fields.JSONField(null=True)
    token_metadata                          = fields.JSONField(null=True)
    token_standard                          = fields.IntEnumField(enum_type=TokenType, index=True, null=True)

    class Meta:
        table = 'token'

class ContractLambda():
    id                                      = fields.IntField(primary_key=True)
    last_updated_at                         = fields.DatetimeField(auto_now=True)
    lambda_name                             = fields.CharField(max_length=128, default="")
    lambda_bytes                            = fields.TextField(default="")

class EquiteezUser(Model):
    id                                      = fields.IntField(primary_key=True)
    address                                 = fields.CharField(max_length=36, index=True)

    class Meta:
        table = 'equiteez_user'

class EquiteezUserBalance(Model):
    id                                      = fields.IntField(primary_key=True)
    user                                    = fields.ForeignKeyField('models.EquiteezUser', related_name='balances')
    token                                   = fields.ForeignKeyField('models.Token', related_name='equiteez_user_balances')
    balance                                 = fields.BigIntField(default=0)

    class Meta:
        table = 'equiteez_user_balance'

class EquiteezUserTokenTransfer(Model):
    id                                      = fields.IntField(primary_key=True)
    from_user                               = fields.ForeignKeyField('models.EquiteezUser', related_name='token_transfer_senders', null=True)
    to_user                                 = fields.ForeignKeyField('models.EquiteezUser', related_name='token_transfer_receivers', null=True)
    token                                   = fields.ForeignKeyField('models.Token', related_name='equiteez_user_token_transfers')
    timestamp                               = fields.DatetimeField()
    level                                   = fields.BigIntField()
    amount                                  = fields.BigIntField()

    class Meta:
        table = 'equiteez_user_token_transfer'
