from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from dipdup.models import Model, fields

from equiteez.shared.event_schema import AggregateType, EventType


def _enum_or_str(value: Union[str, EventType, AggregateType]) -> str:
    if isinstance(value, str):
        return value
    return value.value


class EventsOutbox(Model):
    """
    Outbox table for storing domain events before publishing to the Event Bus.

    Attributes:
        id: Primary key (auto-incrementing)
        event_id: Unique UUID for the event
        event_type: Type of event (BALANCE_UPDATED, ORDER_CREATED, etc.)
        event_version: Schema version for backward compatibility
        occurred_at: When the event occurred in the domain
        source: Source system identifier
        aggregate_type: Type of aggregate (ACCOUNT, ORDER, TRANSFER)
        aggregate_id: Identifier of the aggregate instance
        payload: Event payload as JSON
        published: Whether event has been published to Kafka
        published_at: When the event was published
        retry_count: Failed publish attempts by the relayer
        last_error: Message from the most recent failed publish
        failed_at: Time of the most recent failed publish attempt
        created_at: When the record was created
        updated_at: When the record was last updated
    """

    id = fields.BigIntField(primary_key=True)

    event_id = fields.UUIDField(unique=True, default=uuid4)
    event_type = fields.CharField(max_length=100, index=True)
    event_version = fields.IntField(default=1)
    occurred_at = fields.DatetimeField(index=True)

    source = fields.CharField(max_length=100, default="dipdup-indexer")
    aggregate_type = fields.CharField(max_length=100, index=True)
    aggregate_id = fields.CharField(max_length=255, index=True)

    payload = fields.JSONField()

    published = fields.BooleanField(default=False, index=True)
    published_at = fields.DatetimeField(null=True)
    retry_count = fields.IntField(default=0)
    last_error = fields.TextField(null=True)
    failed_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "events_outbox"
        indexes = [
            ("aggregate_type", "aggregate_id", "occurred_at"),
        ]

    @classmethod
    async def create_event(
        cls,
        event_type: Union[str, EventType],
        aggregate_type: Union[str, AggregateType],
        aggregate_id: str,
        payload: Dict[str, Any],
        event_version: int = 1,
        source: str = "equiteez-indexer",
        occurred_at: Optional[datetime] = None,
    ) -> "EventsOutbox":
        """
        Factory method to create a new outbox event (not saved — call .save()).

        Args:
            event_type: Type of event (e.g., EventType.ORDER_CREATED)
            aggregate_type: Type of aggregate (e.g., AggregateType.ORDER)
            aggregate_id: Identifier of the aggregate
            payload: Event payload dictionary
            event_version: Schema version (default: 1)
            source: Source system (default: "equiteez-indexer")
            occurred_at: When the event occurred (default: now UTC)
        """
        if occurred_at is None:
            occurred_at = datetime.utcnow()

        return cls(
            event_id=uuid4(),
            event_type=_enum_or_str(event_type),
            event_version=event_version,
            occurred_at=occurred_at,
            source=source,
            aggregate_type=_enum_or_str(aggregate_type),
            aggregate_id=str(aggregate_id),
            payload=payload,
        )

    def to_event_envelope(self) -> Dict[str, Any]:
        """Convert the outbox record to the event envelope format."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
        }

    async def mark_published(self) -> None:
        """Mark this event as published (relayer, after successful publish)."""
        self.published = True
        self.published_at = datetime.utcnow()
        self.last_error = None
        self.failed_at = None
        await self.save(
            update_fields=[
                "published",
                "published_at",
                "last_error",
                "failed_at",
                "updated_at",
            ]
        )

    async def mark_failed(self, error: str) -> None:
        """Record a failed publish attempt (relayer)."""
        self.retry_count += 1
        self.last_error = error
        self.failed_at = datetime.utcnow()
        await self.save(
            update_fields=["retry_count", "last_error", "failed_at", "updated_at"]
        )

    @classmethod
    async def get_unpublished_events(
        cls,
        limit: int = 100,
        max_retries: int = 5,
    ) -> list["EventsOutbox"]:
        """Unpublished events for the relayer, ordered by creation time."""
        return (
            await cls.filter(
                published=False,
                retry_count__lt=max_retries,
            )
            .order_by("created_at")
            .limit(limit)
            .all()
        )
