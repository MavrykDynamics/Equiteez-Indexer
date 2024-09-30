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
    # network                                 = fields.CharField(max_length=51, index=True)
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
