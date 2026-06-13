"""
EventBus abstraction with outbox pattern for guaranteed event delivery.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from app.domain.entities.events import DomainEvent


class EventPublishError(Exception):
    """Raised when event publishing fails."""
    pass


class EventSubscriptionError(Exception):
    """Raised when event subscription fails."""
    pass


@dataclass
class PublishResult:
    """Result of event publishing."""
    event_id: uuid.UUID
    published_at: datetime
    partition_key: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class TopicConfig:
    """Configuration for event topic."""
    name: str
    partitions: int = 1
    replication_factor: int = 1
    retention_ms: int = 604800000  # 7 days
    cleanup_policy: str = "delete"


@dataclass
class Subscription:
    """Handle for event subscription."""
    subscription_id: str
    event_type: str
    handler: Callable[[DomainEvent], Awaitable[None]]
    is_active: bool = True


class EventHandler:
    """Protocol for event handlers."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Process a single event."""
        pass


class EventBus(ABC):
    """
    Abstraction over event publishing.
    Implementations: InMemory, Kafka, Redis Streams, AWS EventBridge
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> PublishResult:
        """Publish a single event."""
        pass
    
    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> List[PublishResult]:
        """Publish multiple events in a batch."""
        pass
    
    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None]],
        subscription_id: Optional[str] = None
    ) -> Subscription:
        """Subscribe to an event type."""
        pass
    
    @abstractmethod
    async def create_topic(self, topic: str, config: TopicConfig) -> None:
        """Create a topic/stream."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the event bus."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus."""
        pass


class InMemoryEventBus(EventBus):
    """
    In-memory event bus for development and testing.
    """
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._events: List[DomainEvent] = []
        self._running = False
    
    async def publish(self, event: DomainEvent) -> PublishResult:
        """Publish a single event."""
        self._events.append(event)
        
        # Notify subscribers
        event_type = event.event_type
        if event_type in self._subscriptions:
            for subscription in self._subscriptions[event_type]:
                if subscription.is_active:
                    try:
                        await subscription.handler(event)
                    except Exception as e:
                        # Log error but don't fail
                        print(f"Error in event handler: {e}")
        
        return PublishResult(
            event_id=event.event_id,
            published_at=datetime.utcnow(),
            success=True
        )
    
    async def publish_batch(self, events: List[DomainEvent]) -> List[PublishResult]:
        """Publish multiple events."""
        results = []
        for event in events:
            result = await self.publish(event)
            results.append(result)
        return results
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None]],
        subscription_id: Optional[str] = None
    ) -> Subscription:
        """Subscribe to an event type."""
        if not subscription_id:
            subscription_id = str(uuid.uuid4())
        
        subscription = Subscription(
            subscription_id=subscription_id,
            event_type=event_type,
            handler=handler
        )
        
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        
        self._subscriptions[event_type].append(subscription)
        return subscription
    
    async def create_topic(self, topic: str, config: TopicConfig) -> None:
        """Create a topic (no-op for in-memory)."""
        pass
    
    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
    
    async def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
    
    def get_events(self, event_type: Optional[str] = None) -> List[DomainEvent]:
        """Get published events (for testing)."""
        if event_type:
            return [e for e in self._events if e.event_type == event_type]
        return self._events.copy()


class OutboxRepository:
    """
    Implements the transactional outbox pattern.
    Events are written to the outbox table in the same transaction as the domain event.
    """
    
    def __init__(self, db_session):
        self._session = db_session
    
    async def write_outbox_event(
        self,
        event: DomainEvent,
        idempotency_key: str,
        target_topic: str
    ) -> None:
        """
        Called within the same DB transaction as the domain mutation.
        Guarantees: if domain mutation commits, event WILL be published.
        """
        from app.infrastructure.persistence.models import OutboxMessageModel
        
        outbox_message = OutboxMessageModel(
            aggregate_type=event.event_type,
            aggregate_id=event.event_id,
            event_type=event.event_type,
            payload={
                "event_id": str(event.event_id),
                "tenant_id": str(event.tenant_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_type": event.event_type,
                "payload": event.payload,
                "metadata": event.metadata
            },
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self._session.add(outbox_message)
    
    async def read_pending_events(
        self,
        batch_size: int = 100,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Read events that haven't been successfully published."""
        from app.infrastructure.persistence.models import OutboxMessageModel
        from sqlalchemy import select
        
        query = (
            select(OutboxMessageModel)
            .where(OutboxMessageModel.status == "pending")
            .where(OutboxMessageModel.retry_count < max_retries)
            .order_by(OutboxMessageModel.created_at)
            .limit(batch_size)
        )
        
        result = await self._session.execute(query)
        messages = result.scalars().all()
        
        return [
            {
                "id": msg.id,
                "event_type": msg.event_type,
                "payload": msg.payload,
                "retry_count": msg.retry_count
            }
            for msg in messages
        ]
    
    async def mark_published(self, outbox_id: uuid.UUID) -> None:
        """Mark event as successfully published."""
        from app.infrastructure.persistence.models import OutboxMessageModel
        from sqlalchemy import update
        
        await self._session.execute(
            update(OutboxMessageModel)
            .where(OutboxMessageModel.id == outbox_id)
            .values(
                status="published",
                published_at=datetime.utcnow()
            )
        )
    
    async def mark_failed(
        self,
        outbox_id: uuid.UUID,
        error: str,
        retry_count: int
    ) -> None:
        """Mark event as failed."""
        from app.infrastructure.persistence.models import OutboxMessageModel
        from sqlalchemy import update
        
        new_status = "failed" if retry_count >= 3 else "pending"
        
        await self._session.execute(
            update(OutboxMessageModel)
            .where(OutboxMessageModel.id == outbox_id)
            .values(
                status=new_status,
                retry_count=retry_count,
                error_message=error
            )
        )


class OutboxRelay:
    """
    Reads from outbox and publishes to event bus.
    Runs as a background worker.
    """
    
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        event_bus: EventBus,
        batch_size: int = 100,
        poll_interval_seconds: int = 5
    ):
        self._outbox = outbox_repository
        self._event_bus = event_bus
        self._batch_size = batch_size
        self._poll_interval = poll_interval_seconds
        self._running = False
    
    async def start(self):
        """Start the relay loop."""
        self._running = True
        
        while self._running:
            try:
                await self._process_pending_events()
            except Exception as e:
                print(f"Error in outbox relay: {e}")
            
            import asyncio
            await asyncio.sleep(self._poll_interval)
    
    async def stop(self):
        """Stop the relay loop."""
        self._running = False
    
    async def _process_pending_events(self):
        """Process pending events from outbox."""
        pending = await self._outbox.read_pending_events(self._batch_size)
        
        for message in pending:
            try:
                # Reconstruct event
                event_data = message["payload"]
                event = DomainEvent(
                    event_id=uuid.UUID(event_data["event_id"]),
                    tenant_id=uuid.UUID(event_data["tenant_id"]),
                    occurred_at=datetime.fromisoformat(event_data["occurred_at"]),
                    event_type=event_data["event_type"],
                    payload=event_data["payload"],
                    metadata=event_data.get("metadata", {})
                )
                
                # Publish to event bus
                result = await self._event_bus.publish(event)
                
                if result.success:
                    await self._outbox.mark_published(message["id"])
                else:
                    await self._outbox.mark_failed(
                        message["id"],
                        result.error_message or "Unknown error",
                        message["retry_count"] + 1
                    )
                    
            except Exception as e:
                await self._outbox.mark_failed(
                    message["id"],
                    str(e),
                    message["retry_count"] + 1
                )


class DomainEventPublisher:
    """
    High-level publisher that handles outbox pattern.
    """
    
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        audit_logger=None
    ):
        self._outbox = outbox_repository
        self._audit_logger = audit_logger
    
    async def publish_metric_computed(self, computed_value) -> None:
        """Publish MetricComputed event."""
        from app.domain.entities.events import MetricComputed
        
        event = MetricComputed(
            tenant_id=computed_value.tenant_id,
            computed_value_id=computed_value.entity_id,
            metric_id=computed_value.metric_id,
            metric_version=computed_value.metric_version,
            value=computed_value.value,
            unit=computed_value.unit.value,
            period_start=computed_value.period_start,
            period_end=computed_value.period_end,
            confidence_score=computed_value.confidence_score,
            quality_score=computed_value.quality_score,
            scope={
                "hospital_id": str(computed_value.hospital_id) if computed_value.hospital_id else None,
                "branch_id": str(computed_value.branch_id) if computed_value.branch_id else None,
                "department_id": str(computed_value.department_id) if computed_value.department_id else None
            }
        )
        
        idempotency_key = f"metric_computed:{computed_value.entity_id}"
        await self._outbox.write_outbox_event(event, idempotency_key, "metrics")
    
    async def publish_quality_issue_detected(self, issue) -> None:
        """Publish QualityIssueDetected event."""
        from app.domain.entities.events import QualityIssueDetected
        
        event = QualityIssueDetected(
            tenant_id=issue.tenant_id,
            issue_id=issue.entity_id,
            rule_id=issue.rule_id,
            rule_name=issue.rule_name,
            severity=issue.severity.value,
            entity_type=issue.entity_type,
            entity_id=issue.entity_id,
            field_name=issue.field_name,
            detected_value=str(issue.detected_value),
            expected_value=str(issue.expected_value),
            recommended_action=issue.recommended_action
        )
        
        idempotency_key = f"quality_issue:{issue.entity_id}"
        await self._outbox.write_outbox_event(event, idempotency_key, "quality")
    
    async def publish_data_import_completed(self, import_id, stats) -> None:
        """Publish DataImportCompleted event."""
        from app.domain.entities.events import DataImportCompleted
        
        event = DataImportCompleted(
            import_id=import_id,
            records_processed=stats.get("processed", 0),
            records_succeeded=stats.get("succeeded", 0),
            records_failed=stats.get("failed", 0),
            duration_ms=stats.get("duration_ms", 0),
            quality_score=stats.get("quality_score", 0.0)
        )
        
        idempotency_key = f"import_completed:{import_id}"
        await self._outbox.write_outbox_event(event, idempotency_key, "imports")
