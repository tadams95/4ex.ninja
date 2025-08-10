"""
Async Notification Service for 4ex.ninja

This service provides non-blocking Discord notification delivery with queue processing,
priority routing, circuit breaker pattern, and background workers.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
from collections import deque
import time

from core.entities.signal import Signal
from infrastructure.monitoring.alerts import Alert
from infrastructure.external_services.discord_service import (
    get_discord_service,
    DiscordService,
    UserTier,
    DiscordChannelType,
    DiscordMessage,
)

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels for queue processing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, don't attempt
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class Notification:
    """Notification data structure for queue processing."""

    id: str
    priority: NotificationPriority
    channel_type: DiscordChannelType
    message: DiscordMessage
    signal: Optional[Signal] = None
    alert: Optional[Alert] = None
    additional_context: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0
    max_retries: int = 3


class CircuitBreaker:
    """
    Circuit breaker implementation for Discord API calls.

    Prevents overwhelming a failing Discord API by temporarily stopping
    requests when failure rate is too high.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: tuple = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                logger.warning("Circuit breaker is OPEN, skipping Discord call")
                return False

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            logger.error(f"Circuit breaker caught exception: {str(e)}")
            return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return False
        return time.time() - self.last_failure_time >= self.timeout

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker transitioning to CLOSED after successful call")
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(
                f"Circuit breaker tripped: {self.failure_count} failures, "
                f"state changed to OPEN for {self.timeout}s"
            )


class AsyncNotificationService:
    """
    Async notification service with queue processing and circuit breaker.

    This service replaces blocking Discord calls with async queue processing,
    implements priority routing, and provides resilient notification delivery.
    """

    def __init__(self, max_queue_size: int = 1000, worker_count: int = 2):
        self.discord_service = get_discord_service()
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Priority queues for different notification priorities
        self.queues = {
            NotificationPriority.URGENT: asyncio.Queue(maxsize=max_queue_size // 4),
            NotificationPriority.HIGH: asyncio.Queue(maxsize=max_queue_size // 4),
            NotificationPriority.NORMAL: asyncio.Queue(maxsize=max_queue_size // 2),
            NotificationPriority.LOW: asyncio.Queue(maxsize=max_queue_size // 4),
        }

        # Background worker tasks
        self.workers: List[asyncio.Task] = []
        self.worker_count = worker_count
        self.running = False

        # Metrics
        self.metrics = {
            "notifications_queued": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "queue_depth": 0,
            "circuit_breaker_trips": 0,
        }

        # Rate limiting
        self.rate_limits = {
            DiscordChannelType.SIGNALS_FREE: deque(maxlen=20),  # 20 per minute
            DiscordChannelType.SIGNALS_PREMIUM: deque(maxlen=30),  # 30 per minute
            DiscordChannelType.ALERTS_CRITICAL: deque(maxlen=10),  # 10 per minute
            DiscordChannelType.ALERTS_GENERAL: deque(maxlen=15),  # 15 per minute
            DiscordChannelType.MARKET_ANALYSIS: deque(maxlen=10),  # 10 per minute
            DiscordChannelType.SYSTEM_STATUS: deque(maxlen=5),  # 5 per minute
            DiscordChannelType.GENERAL: deque(maxlen=30),  # 30 per minute
        }

    async def start(self):
        """Start the background workers."""
        if self.running:
            logger.warning("AsyncNotificationService is already running")
            return

        self.running = True
        logger.info(f"Starting {self.worker_count} notification workers")

        for i in range(self.worker_count):
            worker = asyncio.create_task(self._notification_worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info("AsyncNotificationService started successfully")

    async def stop(self):
        """Stop the background workers and process remaining notifications."""
        if not self.running:
            return

        logger.info("Stopping AsyncNotificationService...")
        self.running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()
        logger.info("AsyncNotificationService stopped")

    async def queue_notification(
        self,
        signal_data: Union[Signal, Alert],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_tier: UserTier = UserTier.FREE,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Queue a notification for async processing.

        Args:
            signal_data: Signal or Alert to send
            priority: Notification priority
            user_tier: User tier for channel routing
            additional_context: Additional context data

        Returns:
            bool: True if queued successfully, False if queue is full
        """
        try:
            # Create notification object
            notification_id = self._generate_notification_id(signal_data)

            if isinstance(signal_data, Signal):
                channel_type = self._get_signal_channel(signal_data, user_tier)
                message = self._create_signal_message(signal_data, additional_context)
                notification = Notification(
                    id=notification_id,
                    priority=priority,
                    channel_type=channel_type,
                    message=message,
                    signal=signal_data,
                    additional_context=additional_context,
                )
            elif isinstance(signal_data, Alert):
                channel_type = self._get_alert_channel(signal_data)
                message = self._create_alert_message(signal_data)
                notification = Notification(
                    id=notification_id,
                    priority=priority,
                    channel_type=channel_type,
                    message=message,
                    alert=signal_data,
                    additional_context=additional_context,
                )
            else:
                logger.error(f"Unsupported signal_data type: {type(signal_data)}")
                return False

            # Queue notification based on priority
            queue = self.queues[priority]

            if queue.full():
                logger.warning(f"Notification queue for {priority.value} is full")
                return False

            await queue.put(notification)
            self.metrics["notifications_queued"] += 1
            self._update_queue_depth_metric()

            logger.debug(
                f"Queued {priority.value} notification {notification_id} "
                f"for {channel_type.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Error queueing notification: {str(e)}")
            return False

    async def _notification_worker(self, worker_name: str):
        """
        Background worker that processes notifications from queues.

        Workers process notifications in priority order: URGENT -> HIGH -> NORMAL -> LOW
        """
        logger.info(f"Notification worker {worker_name} started")

        while self.running:
            try:
                notification = await self._get_next_notification()

                if notification is None:
                    # No notifications available, short sleep
                    await asyncio.sleep(0.1)
                    continue

                success = await self._process_notification(notification, worker_name)

                if not success and notification.retry_count < notification.max_retries:
                    # Retry failed notification
                    notification.retry_count += 1
                    await self._requeue_notification(notification)
                    logger.debug(
                        f"Requeued notification {notification.id} "
                        f"(retry {notification.retry_count}/{notification.max_retries})"
                    )
                elif not success:
                    # Max retries exceeded
                    logger.error(
                        f"Notification {notification.id} failed after "
                        f"{notification.max_retries} retries"
                    )
                    self.metrics["notifications_failed"] += 1
                else:
                    self.metrics["notifications_sent"] += 1

                self._update_queue_depth_metric()

            except asyncio.CancelledError:
                logger.info(f"Notification worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in notification worker {worker_name}: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loop

        logger.info(f"Notification worker {worker_name} stopped")

    async def _get_next_notification(self) -> Optional[Notification]:
        """Get the next notification from queues in priority order."""
        priority_order = [
            NotificationPriority.URGENT,
            NotificationPriority.HIGH,
            NotificationPriority.NORMAL,
            NotificationPriority.LOW,
        ]

        for priority in priority_order:
            queue = self.queues[priority]
            try:
                return queue.get_nowait()
            except asyncio.QueueEmpty:
                continue

        return None

    async def _process_notification(
        self, notification: Notification, worker_name: str
    ) -> bool:
        """
        Process a single notification with circuit breaker protection.

        Args:
            notification: Notification to process
            worker_name: Name of processing worker

        Returns:
            bool: Success status
        """
        # Check rate limiting
        if not self._check_rate_limit(notification.channel_type):
            logger.debug(
                f"Rate limit hit for {notification.channel_type.value}, "
                f"delaying notification {notification.id}"
            )
            await asyncio.sleep(1)  # Brief delay for rate limiting
            return await self._requeue_notification(notification)

        # Process with circuit breaker
        logger.debug(
            f"Worker {worker_name} processing notification {notification.id} "
            f"for {notification.channel_type.value}"
        )

        success = await self.circuit_breaker.call(
            self.discord_service.send_webhook_message,
            notification.channel_type,
            notification.message,
        )

        if success:
            self._record_rate_limit(notification.channel_type)
            logger.debug(f"Successfully sent notification {notification.id}")
        else:
            logger.warning(f"Failed to send notification {notification.id}")
            if self.circuit_breaker.state == CircuitBreakerState.OPEN:
                self.metrics["circuit_breaker_trips"] += 1

        return success

    async def _requeue_notification(self, notification: Notification) -> bool:
        """Requeue a notification for retry."""
        try:
            queue = self.queues[notification.priority]
            if not queue.full():
                await queue.put(notification)
                return True
            else:
                logger.warning(
                    f"Cannot requeue notification {notification.id}: queue full"
                )
                return False
        except Exception as e:
            logger.error(f"Error requeuing notification {notification.id}: {str(e)}")
            return False

    def _check_rate_limit(self, channel_type: DiscordChannelType) -> bool:
        """Check if we can send to this channel without hitting rate limits."""
        rate_limit_queue = self.rate_limits.get(channel_type)
        if not rate_limit_queue:
            return True

        current_time = time.time()

        # Remove entries older than 1 minute
        while rate_limit_queue and current_time - rate_limit_queue[0] > 60:
            rate_limit_queue.popleft()

        # Check if we're at the limit
        max_len = rate_limit_queue.maxlen
        return len(rate_limit_queue) < (
            max_len if max_len is not None else float("inf")
        )

    def _record_rate_limit(self, channel_type: DiscordChannelType):
        """Record a message send for rate limiting."""
        rate_limit_queue = self.rate_limits.get(channel_type)
        if rate_limit_queue is not None:
            rate_limit_queue.append(time.time())

    def _get_signal_channel(
        self, signal: Signal, user_tier: UserTier
    ) -> DiscordChannelType:
        """Determine appropriate Discord channel for signal."""
        if (
            user_tier == UserTier.PREMIUM
            and signal.confidence_score
            and signal.confidence_score >= 0.8
        ):
            return DiscordChannelType.SIGNALS_PREMIUM
        return DiscordChannelType.SIGNALS_FREE

    def _get_alert_channel(self, alert: Alert) -> DiscordChannelType:
        """Determine appropriate Discord channel for alert."""
        from infrastructure.monitoring.alerts import AlertSeverity

        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return DiscordChannelType.ALERTS_CRITICAL
        return DiscordChannelType.ALERTS_GENERAL

    def _create_signal_message(
        self, signal: Signal, additional_context: Optional[Dict[str, Any]] = None
    ) -> DiscordMessage:
        """Create Discord message for signal."""
        embed = self.discord_service._create_signal_embed(signal, additional_context)

        return DiscordMessage(
            content=f"🚨 New {signal.signal_type.value} signal: {signal.pair}",
            embeds=[embed],
            channel_type=DiscordChannelType.SIGNALS_FREE,  # Will be overridden
            priority=(
                "high"
                if signal.confidence_score and signal.confidence_score > 0.8
                else "normal"
            ),
        )

    def _create_alert_message(self, alert: Alert) -> DiscordMessage:
        """Create Discord message for alert."""
        embed = self.discord_service._create_alert_embed(alert)

        return DiscordMessage(
            content=f"🚨 {alert.severity.value.upper()} Alert",
            embeds=[embed],
            channel_type=DiscordChannelType.ALERTS_GENERAL,  # Will be overridden
            priority="urgent" if alert.severity.value == "CRITICAL" else "high",
        )

    def _generate_notification_id(self, data: Union[Signal, Alert]) -> str:
        """Generate unique notification ID."""
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        if isinstance(data, Signal):
            return f"signal_{data.signal_id}_{timestamp}"
        elif isinstance(data, Alert):
            return f"alert_{data.alert_id}_{timestamp}"
        else:
            return f"notification_{timestamp}"

    def _update_queue_depth_metric(self):
        """Update queue depth metric."""
        total_depth = sum(queue.qsize() for queue in self.queues.values())
        self.metrics["queue_depth"] = total_depth

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        self._update_queue_depth_metric()

        return {
            **self.metrics,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "queue_sizes": {
                priority.value: queue.qsize() for priority, queue in self.queues.items()
            },
            "running": self.running,
            "worker_count": len(self.workers),
        }


# Global service instance
_async_notification_service: Optional[AsyncNotificationService] = None


def get_async_notification_service() -> AsyncNotificationService:
    """Get or create the global async notification service."""
    global _async_notification_service
    if _async_notification_service is None:
        _async_notification_service = AsyncNotificationService()
    return _async_notification_service


async def cleanup_async_notification_service():
    """Cleanup the global async notification service."""
    global _async_notification_service
    if _async_notification_service:
        await _async_notification_service.stop()
        _async_notification_service = None
