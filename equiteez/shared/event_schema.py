from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class EventType(str, Enum):
    """Enumeration of all event types in the system."""

    BALANCE_UPDATED = "BALANCE_UPDATED"

    ORDER_CREATED = "ORDER_CREATED"
    ORDER_UPDATED = "ORDER_UPDATED"
    ORDER_CANCELLED = "ORDER_CANCELLED"

    TRANSFER_CREATED = "TRANSFER_CREATED"

    # Super Admin — aggregate_id = Super Admin contract address (KT1…).
    #
    # Suggested common payload fields: level, operation_hash, timestamp, entrypoint (Michelson).
    #
    # Handler → event type (when emitting from the indexer):
    #   origination → SUPER_ADMIN_CREATED
    #   update_metadata → SUPER_ADMIN_METADATA_UPDATED
    #   set_lambda → SUPER_ADMIN_LAMBDA_UPDATED
    #   * via create_super_admin_action (proposal in ledger) → SUPER_ADMIN_ACTION_PROPOSED
    #       (set_super_admin, set_general_admin, set_contract_admin, add/remove signatory,
    #        remove_general/contract_admin, update_config, set_token_kyc_address,
    #        kill_token, flush_action, claim_super_admin — disambiguate with payload.proposal_kind)
    #   sign_action → SUPER_ADMIN_ACTION_SIGNED (+ on status transition to EXECUTED/FLUSHED)
    #   flush_action (executed path) / storage → SUPER_ADMIN_ACTION_FLUSHED | SUPER_ADMIN_ACTION_EXECUTED
    SUPER_ADMIN_CREATED = "SUPER_ADMIN_CREATED"
    SUPER_ADMIN_METADATA_UPDATED = "SUPER_ADMIN_METADATA_UPDATED"
    SUPER_ADMIN_LAMBDA_UPDATED = "SUPER_ADMIN_LAMBDA_UPDATED"

    SUPER_ADMIN_SIGNATORY_ADDED = "SUPER_ADMIN_SIGNATORY_ADDED"
    SUPER_ADMIN_SIGNATORY_REMOVED = "SUPER_ADMIN_SIGNATORY_REMOVED"
    SUPER_ADMIN_GENERAL_ADMIN_ADDED = "SUPER_ADMIN_GENERAL_ADMIN_ADDED"
    SUPER_ADMIN_GENERAL_ADMIN_REMOVED = "SUPER_ADMIN_GENERAL_ADMIN_REMOVED"
    SUPER_ADMIN_CONTRACT_ADMIN_ADDED = "SUPER_ADMIN_CONTRACT_ADMIN_ADDED"
    SUPER_ADMIN_CONTRACT_ADMIN_REMOVED = "SUPER_ADMIN_CONTRACT_ADMIN_REMOVED"

    SUPER_ADMIN_ACTION_PROPOSED = "SUPER_ADMIN_ACTION_PROPOSED"
    SUPER_ADMIN_ACTION_SIGNED = "SUPER_ADMIN_ACTION_SIGNED"
    SUPER_ADMIN_ACTION_EXECUTED = "SUPER_ADMIN_ACTION_EXECUTED"
    SUPER_ADMIN_ACTION_FLUSHED = "SUPER_ADMIN_ACTION_FLUSHED"


class AggregateType(str, Enum):
    """Enumeration of all aggregate types in the system."""

    ACCOUNT = "ACCOUNT"
    ORDER = "ORDER"
    TRANSFER = "TRANSFER"
    SUPER_ADMIN = "SUPER_ADMIN"


class EventEnvelope:
    """
    Standard event envelope format for all domain events.

    Attributes:
        event_id: Unique UUID identifier for the event
        event_type: Type of event (from EventType enum)
        event_version: Schema version for backward compatibility
        occurred_at: ISO datetime string when event occurred
        source: Source system identifier
        aggregate_type: Type of aggregate (from AggregateType enum)
        aggregate_id: Identifier of the aggregate instance
        payload: Event-specific payload data
    """

    def __init__(
        self,
        event_id: UUID,
        event_type: EventType,
        aggregate_type: AggregateType,
        aggregate_id: str,
        payload: Dict[str, Any],
        event_version: int = 1,
        occurred_at: Optional[datetime] = None,
        source: str = "dipdup-indexer",
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.event_version = event_version
        self.occurred_at = occurred_at or datetime.utcnow()
        self.source = source
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event envelope to a dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "aggregate_type": self.aggregate_type.value,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        """Create an event envelope from a dictionary."""
        return cls(
            event_id=UUID(data["event_id"]),
            event_type=EventType(data["event_type"]),
            event_version=data.get("event_version", 1),
            occurred_at=datetime.fromisoformat(
                data["occurred_at"].replace("Z", "+00:00")
            ),
            source=data.get("source", "dipdup-indexer"),
            aggregate_type=AggregateType(data["aggregate_type"]),
            aggregate_id=data["aggregate_id"],
            payload=data["payload"],
        )


TOPIC_MAPPING = {
    AggregateType.ACCOUNT: "balances.events",
    AggregateType.ORDER: "orders.events",
    AggregateType.TRANSFER: "transfers.events",
    AggregateType.SUPER_ADMIN: "super_admin.events",
}


def get_topic_for_aggregate(aggregate_type: AggregateType) -> str:
    """Get the Event Bus topic name for an aggregate type."""
    return TOPIC_MAPPING.get(aggregate_type, "events.default")


_SUPER_ADMIN_EVENT_TYPES = frozenset(
    {
        EventType.SUPER_ADMIN_CREATED,
        EventType.SUPER_ADMIN_METADATA_UPDATED,
        EventType.SUPER_ADMIN_LAMBDA_UPDATED,
        EventType.SUPER_ADMIN_SIGNATORY_ADDED,
        EventType.SUPER_ADMIN_SIGNATORY_REMOVED,
        EventType.SUPER_ADMIN_GENERAL_ADMIN_ADDED,
        EventType.SUPER_ADMIN_GENERAL_ADMIN_REMOVED,
        EventType.SUPER_ADMIN_CONTRACT_ADMIN_ADDED,
        EventType.SUPER_ADMIN_CONTRACT_ADMIN_REMOVED,
        EventType.SUPER_ADMIN_ACTION_PROPOSED,
        EventType.SUPER_ADMIN_ACTION_SIGNED,
        EventType.SUPER_ADMIN_ACTION_EXECUTED,
        EventType.SUPER_ADMIN_ACTION_FLUSHED,
    }
)


def get_topic_for_event_type(event_type: EventType) -> str:
    """Get the Event Bus topic name for an event type."""
    if event_type in [EventType.BALANCE_UPDATED]:
        return TOPIC_MAPPING[AggregateType.ACCOUNT]
    elif event_type in [
        EventType.ORDER_CREATED,
        EventType.ORDER_UPDATED,
        EventType.ORDER_CANCELLED,
    ]:
        return TOPIC_MAPPING[AggregateType.ORDER]
    elif event_type == EventType.TRANSFER_CREATED:
        return TOPIC_MAPPING[AggregateType.TRANSFER]
    elif event_type in _SUPER_ADMIN_EVENT_TYPES:
        return TOPIC_MAPPING[AggregateType.SUPER_ADMIN]
    else:
        return "events.default"
