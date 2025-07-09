from dipdup.models import Model, fields
from enum import IntEnum

###
# Shared Enums
###


class TokenType(IntEnum):
    FA12 = 0
    FA2 = 1
    MAV = 2


class TransferType(IntEnum):
    TRANSFER = 0
    MINT = 1
    BURN = 2


###
# Shared Tables
###


class Token(Model):
    """
    Stores information about all tokens tracked by the indexer.
    This table contains metadata and configuration for all tokens in Equiteez,
    including FA1.2, FA2, and Mavryk-specific tokens. Each token is identified by its
    contract address and token ID (for FA2 tokens with multiple token types).
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Mavryk contract address of the token
    address = fields.CharField(max_length=36, index=True)

    # Token ID (for FA2 tokens with multiple token types)
    token_id = fields.SmallIntField(default=0)

    # Token metadata in JSON format
    metadata = fields.JSONField(null=True)

    # Additional token metadata
    token_metadata = fields.JSONField(null=True)

    # Token standard type (FA12, FA2, MAV)
    token_standard = fields.IntEnumField(enum_type=TokenType, index=True, null=True)

    class Meta:
        table = "token"
        indexes = [
            ("address", "token_id"),
        ]


class ContractLambda:
    """
    Abstract base class for storing contract lambda functions.
    This class provides a common interface for storing lambda functions associated
    with smart contracts. Lambda functions are serialized and stored as text.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Timestamp of last lambda update
    last_updated_at = fields.DatetimeField(auto_now=True)

    # Name/identifier of the lambda function
    lambda_name = fields.CharField(max_length=128, default="")

    # Serialized lambda function bytes
    lambda_bytes = fields.TextField(default="")


class EntrypointStatus:
    """
    Abstract base class for tracking entrypoint pause status.
    This class provides a common interface for tracking whether specific entrypoints
    of smart contracts are paused or active.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Name of the contract entrypoint
    entrypoint = fields.TextField()

    # Whether the entrypoint is currently paused
    paused = fields.BooleanField(default=False)


class EquiteezUser(Model):
    """
    Represents an Equiteez account tracked by the indexer.
    This table stores all users who interact with Equiteez. Each user
    is identified by their Mavryk address (public key hash) and can participate in
    trading, KYC verification, and other platform activities.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Public key hash of the user (Mavryk address)
    address = fields.CharField(max_length=36, index=True, unique=True)

    class Meta:
        table = "equiteez_user"


class EquiteezUserBalance(Model):
    """
    Tracks token balances for each user.
    This table maintains the current balance of each token for every user in
    Equiteez. Balances are stored in the smallest unit (e.g., micromav for MVRK)
    and are updated whenever transfers occur.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Reference to the user
    user = fields.ForeignKeyField("models.EquiteezUser", related_name="balances")

    # Reference to the token
    token = fields.ForeignKeyField(
        "models.Token", related_name="equiteez_user_balances"
    )

    # Current token balance (in smallest unit)
    balance = fields.BigIntField(default=0)

    class Meta:
        table = "equiteez_user_balance"
        indexes = [
            ("user_id", "token_id"),
        ]


class EquiteezUserTokenTransfer(Model):
    """
    Tracks all token transfers between users.
    This table maintains a complete audit trail of all token transfers in Equiteez,
    including transfers between users, minting operations, and burning operations.
    Each transfer is recorded with its timestamp, blockchain level, and amount.
    """

    # Primary key identifier
    id = fields.IntField(primary_key=True)

    # Sender user (null for mints)
    from_user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="token_transfer_senders", null=True
    )

    # Receiver user (null for burns)
    to_user = fields.ForeignKeyField(
        "models.EquiteezUser", related_name="token_transfer_receivers", null=True
    )

    # Token being transferred
    token = fields.ForeignKeyField(
        "models.Token", related_name="equiteez_user_token_transfers"
    )

    # Transfer timestamp
    timestamp = fields.DatetimeField(index=True)

    # Mavryk blockchain level
    level = fields.BigIntField(index=True)

    # Type of transfer (TRANSFER/MINT/BURN)
    transfer_type = fields.IntEnumField(enum_type=TransferType, index=True)

    # Transfer amount (in smallest unit)
    amount = fields.BigIntField()

    class Meta:
        table = "equiteez_user_token_transfer"
        indexes = [
            ("from_user_id", "token_id"),
            ("to_user_id", "token_id"),
            ("token_id", "timestamp"),
        ]
