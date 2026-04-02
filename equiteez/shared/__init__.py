"""Shared utilities and schemas for event-driven architecture."""

from equiteez.shared.event_schema import (
    EventType,
    AggregateType,
    EventEnvelope,
    get_topic_for_aggregate,
    get_topic_for_event_type,
    TOPIC_MAPPING,
)

__all__ = [
    "EventType",
    "AggregateType",
    "EventEnvelope",
    "get_topic_for_aggregate",
    "get_topic_for_event_type",
    "TOPIC_MAPPING",
]
