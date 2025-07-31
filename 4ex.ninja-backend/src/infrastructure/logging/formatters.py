"""
Custom log formatters for different environments and use cases.
Provides colored development output, structured JSON for production,
and enhanced error formatting with stack traces.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional


class BaseFormatter(logging.Formatter):
    """Base formatter with common functionality."""

    def format_timestamp(self, record: logging.LogRecord) -> str:
        """Format timestamp in ISO format."""
        dt = datetime.fromtimestamp(record.created)
        return dt.isoformat()

    def get_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields from log record."""
        extra = {}

        # Standard fields to exclude
        excluded_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "message",
        }

        for key, value in record.__dict__.items():
            if key not in excluded_fields and not key.startswith("_"):
                extra[key] = value

        return extra


class DevelopmentFormatter(BaseFormatter):
    """Formatter for development environment with colored output and readability."""

    # Color codes for different log levels
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for development environment."""

        # Format timestamp
        timestamp = self.format_timestamp(record)

        # Get color for log level
        color = self.COLORS.get(record.levelname, "") if self.use_colors else ""
        reset = self.RESET if self.use_colors else ""

        # Format the basic log message
        message = record.getMessage()

        # Build the log line
        log_parts = [
            f"{timestamp}",
            f"{color}[{record.levelname}]{reset}",
            f"{record.name}:{record.lineno}",
            f"{record.funcName}()",
            f"- {message}",
        ]

        log_line = " ".join(log_parts)

        # Add extra fields if present
        extra = self.get_extra_fields(record)
        if extra:
            extra_str = " | ".join([f"{k}={v}" for k, v in extra.items()])
            log_line += f" | {extra_str}"

        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_line += f"\n{exc_text}"

        return log_line


class ProductionFormatter(BaseFormatter):
    """Formatter for production environment with JSON structure."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for production environment."""

        log_data = {
            "timestamp": self.format_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "thread": record.thread,
            "process": record.process,
        }

        # Add extra fields
        extra = self.get_extra_fields(record)
        if extra:
            log_data["extra"] = extra

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))


class ErrorFormatter(BaseFormatter):
    """Enhanced formatter for error logs with detailed context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format error log with enhanced context and stack traces."""

        lines = []

        # Header with timestamp and level
        timestamp = self.format_timestamp(record)
        lines.append(f"=== {record.levelname} at {timestamp} ===")

        # Basic information
        lines.append(f"Logger: {record.name}")
        lines.append(f"Module: {record.module}")
        lines.append(f"Function: {record.funcName}() at line {record.lineno}")
        lines.append(f"Thread: {record.threadName} ({record.thread})")
        lines.append(f"Process: {record.processName} ({record.process})")

        # Message
        lines.append(f"Message: {record.getMessage()}")

        # Extra context if available
        extra = self.get_extra_fields(record)
        if extra:
            lines.append("Context:")
            for key, value in extra.items():
                lines.append(f"  {key}: {value}")

        # Exception details if present
        if record.exc_info:
            lines.append("Exception Details:")
            exc_type, exc_value, exc_traceback = record.exc_info

            if exc_type:
                lines.append(f"  Type: {exc_type.__name__}")
            if exc_value:
                lines.append(f"  Message: {str(exc_value)}")

            # Full traceback
            if exc_traceback:
                lines.append("  Traceback:")
                tb_lines = traceback.format_exception(
                    exc_type, exc_value, exc_traceback
                )
                for tb_line in tb_lines:
                    lines.append(f"    {tb_line.rstrip()}")

        # Stack info if available
        if record.stack_info:
            lines.append("Stack Info:")
            for stack_line in record.stack_info.split("\n"):
                if stack_line.strip():
                    lines.append(f"  {stack_line}")

        lines.append("=" * 50)

        return "\n".join(lines)


class PerformanceFormatter(BaseFormatter):
    """Formatter specifically for performance monitoring logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format performance log record with timing information."""

        timestamp = self.format_timestamp(record)
        message = record.getMessage()

        # Extract performance-related fields
        extra = self.get_extra_fields(record)

        performance_data = {
            "timestamp": timestamp,
            "message": message,
            "module": record.module,
            "function": record.funcName,
        }

        # Add timing information if available
        timing_fields = [
            "duration",
            "start_time",
            "end_time",
            "cpu_time",
            "memory_usage",
        ]
        for field in timing_fields:
            if field in extra:
                performance_data[field] = extra[field]

        # Add request/response information if available
        request_fields = [
            "method",
            "path",
            "status_code",
            "response_size",
            "user_id",
            "correlation_id",
        ]
        for field in request_fields:
            if field in extra:
                performance_data[field] = extra[field]

        return json.dumps(performance_data, ensure_ascii=False, separators=(",", ":"))


class AuditFormatter(BaseFormatter):
    """Formatter for audit trail logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format audit log record with user context and actions."""

        timestamp = self.format_timestamp(record)
        message = record.getMessage()
        extra = self.get_extra_fields(record)

        audit_data = {
            "timestamp": timestamp,
            "action": message,
            "logger": record.name,
            "level": record.levelname,
        }

        # Add user context
        user_fields = ["user_id", "username", "session_id", "ip_address", "user_agent"]
        for field in user_fields:
            if field in extra:
                audit_data[field] = extra[field]

        # Add action context
        action_fields = [
            "resource",
            "resource_id",
            "method",
            "path",
            "status",
            "changes",
        ]
        for field in action_fields:
            if field in extra:
                audit_data[field] = extra[field]

        # Add any remaining extra fields
        remaining_extra = {
            k: v
            for k, v in extra.items()
            if k not in user_fields and k not in action_fields
        }
        if remaining_extra:
            audit_data["context"] = json.dumps(remaining_extra)

        return json.dumps(audit_data, ensure_ascii=False, separators=(",", ":"))
