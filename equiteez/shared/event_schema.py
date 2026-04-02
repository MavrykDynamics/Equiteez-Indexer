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


class AggregateType(str, Enum):
    """Enumeration of all aggregate types in the system."""

    ACCOUNT = "ACCOUNT"
    ORDER = "ORDER"
    TRANSFER = "TRANSFER"


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
}


def get_topic_for_aggregate(aggregate_type: AggregateType) -> str:
    """Get the Event Bus topic name for an aggregate type."""
    return TOPIC_MAPPING.get(aggregate_type, "events.default")


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
    else:
        return "events.default"
