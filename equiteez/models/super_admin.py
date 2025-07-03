from dipdup.models import Model, fields
from enum import IntEnum
from equiteez.models.shared import ContractLambda

###
# SuperAdmin Enums
###


class ActionStatus(IntEnum):
    FLUSHED = 0
    EXECUTED = 1
    PENDING = 2


###
# SuperAdmin Tables
###


class SuperAdmin(Model):
    """
    Super admin contract configuration and state.
    This table stores the configuration and current state of super admin contracts,
    which provide administrative control over Equiteez. Super admins
    can perform operations like updating contracts, minting/burning tokens, and
    pausing/unpausing contracts across the platform.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Super admin contract address
    address = fields.CharField(max_length=36, index=True)

    # Contract metadata
    metadata = fields.JSONField(null=True)

    # Number of signatories required
    signatory_size = fields.BigIntField(default=0)

    # Counter for actions
    action_counter = fields.BigIntField(default=0)

    # Threshold for action execution
    threshold = fields.BigIntField(default=0)

    # Action expiry time in seconds
    action_expiry_in_seconds = fields.BigIntField(default=0)

    class Meta:
        table = "super_admin"


class SuperAdminLambda(Model, ContractLambda):
    """
    Stores lambda functions for a super admin contract.
    This table stores lambda functions associated with super admin contracts.
    """

    # Reference to super admin contract
    contract = fields.ForeignKeyField("models.SuperAdmin", related_name="lambdas")

    class Meta:
        table = "super_admin_lambda"


class SuperAdminSignatory(Model):
    """
    Represents signatories who can approve administrative actions.
    This table stores information about signatories who are authorized to approve
    administrative actions in the super admin system. Signatories can initiate
    actions and sign off on actions initiated by other signatories.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to super admin contract
    super_admin = fields.ForeignKeyField(
        "models.SuperAdmin", related_name="signatories"
    )

    # Signatory user
    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="super_admin_signatories"
    )

    # Signatory name
    name = fields.TextField(default="")

    # Whether signatory is active
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "super_admin_signatory"


class SuperAdminGeneralAdmin(Model):
    """
    Represents general administrators in the super admin system.
    This table stores information about general administrators who have
    administrative privileges Equiteez.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to super admin contract
    super_admin = fields.ForeignKeyField(
        "models.SuperAdmin", related_name="general_admins"
    )

    # General admin user
    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="super_admin_general_admins"
    )

    class Meta:
        table = "super_admin_general_admin"


class SuperAdminContractAdmin(Model):
    """
    Represents contract-specific administrators.
    This table stores information about administrators who have
    administrative privileges for specific contracts in the system.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to super admin contract
    super_admin = fields.ForeignKeyField(
        "models.SuperAdmin", related_name="contract_admins"
    )

    # Contract admin user
    user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="super_admin_contract_admins"
    )

    # Contract address this admin manages
    contract_address = fields.CharField(max_length=36, index=True)

    class Meta:
        table = "super_admin_contract_admin"


class SuperAdminSignatoryAction(Model):
    """
    Tracks actions that require signatory approval.
    This table stores all administrative actions that require approval from
    multiple signatories before execution. Actions can include contract updates,
    token minting/burning, and system-wide configuration changes.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to super admin contract
    super_admin = fields.ForeignKeyField(
        "models.SuperAdmin", related_name="signatory_actions"
    )

    # Signatory who initiated the action
    initiator = fields.ForeignKeyField(
        "models.SuperAdminSignatory", related_name="signatory_actions"
    )

    # Unique action identifier
    action_id = fields.BigIntField(default=0)

    # Type of action
    action_type = fields.TextField(default="")

    # Whether action has been executed
    executed = fields.BooleanField(default=False)

    # Action status (FLUSHED/EXECUTED/PENDING)
    status = fields.IntEnumField(
        enum_type=ActionStatus, index=True, default=ActionStatus.PENDING
    )

    # Number of signers who approved
    signers_count = fields.BigIntField(default=0)

    # Action start timestamp
    start_datetime = fields.DatetimeField(null=True)

    # Blockchain level when action started
    start_level = fields.BigIntField(default=0)

    # Action execution timestamp
    executed_datetime = fields.DatetimeField(null=True)

    # Blockchain level when action was executed
    executed_level = fields.BigIntField(null=True)

    # Action expiration timestamp
    expiration_datetime = fields.DatetimeField(null=True)

    class Meta:
        table = "super_admin_signatory_action"


class SuperAdminSignatoryActionData(Model):
    """
    Stores additional data for signatory actions.
    This table stores supplementary data associated with signatory actions,
    such as action parameters and serialized data.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to the signatory action
    action = fields.ForeignKeyField(
        "models.SuperAdminSignatoryAction", related_name="data"
    )

    # Data name/identifier
    name = fields.TextField()

    # Serialized action data
    bytes = fields.TextField()

    class Meta:
        table = "super_admin_signatory_action_data"


class SuperAdminSignature(Model):
    """
    Tracks signatures on signatory actions.
    This table stores signatures from signatories on administrative actions,
    tracking which signatories have approved specific actions.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to super admin contract
    super_admin = fields.ForeignKeyField("models.SuperAdmin", related_name="signatures")

    # Signatory who provided the signature
    signatory = fields.ForeignKeyField(
        "models.SuperAdminSignatory", related_name="signatures"
    )

    # Action being signed
    action = fields.ForeignKeyField(
        "models.SuperAdminSignatoryAction", related_name="signatures"
    )

    class Meta:
        table = "super_admin_signature"
