"""
Fast JSON serialization utilities for improved API performance.

This module provides optimized JSON serialization using orjson
when available, falling back to the standard json module.
"""

import json
import logging
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Union, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

# Try to import orjson, fall back to standard json if not available
try:
    import orjson  # type: ignore

    ORJSON_AVAILABLE = True
    logger.info("orjson available - using fast JSON serialization")
except ImportError:
    orjson = None
    ORJSON_AVAILABLE = False
    logger.warning("orjson not available - falling back to standard json")


class FastJSONResponse(JSONResponse):
    """
    Optimized JSON response class using orjson when available.

    Falls back to standard JSON serialization if orjson is not installed.
    Provides significant performance improvements for large JSON payloads.
    """

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        """
        Render content to JSON bytes using the fastest available method.

        Args:
            content: Content to serialize to JSON

        Returns:
            JSON bytes
        """
        if content is None:
            return b"null"

        # Use orjson if available for better performance
        if ORJSON_AVAILABLE and orjson is not None:
            try:
                return orjson.dumps(
                    content, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
                )
            except (TypeError, ValueError):
                # Fall back to standard JSON for complex objects
                pass

        # Fallback to standard JSON with FastAPI's encoder
        try:
            encoded_content = jsonable_encoder(content)
            return json.dumps(
                encoded_content,
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")
        except Exception as e:
            # Create error response
            error_content = {
                "error": "JSON serialization failed",
                "detail": str(e),
                "type": "serialization_error",
            }
            if ORJSON_AVAILABLE and orjson is not None:
                return orjson.dumps(error_content)
            else:
                return json.dumps(error_content).encode("utf-8")


def create_fast_json_response(
    content: Any, status_code: int = 200, headers: Optional[dict] = None
) -> FastJSONResponse:
    """
    Create a FastJSONResponse with optional headers.

    Args:
        content: Data to serialize
        status_code: HTTP status code
        headers: Additional headers

    Returns:
        FastJSONResponse instance
    """
    response_headers = {}

    # Add cache control for API responses
    if status_code == 200:
        response_headers["Cache-Control"] = "public, max-age=60"

    # Merge with provided headers
    if headers:
        response_headers.update(headers)

    return FastJSONResponse(
        content=content,
        status_code=status_code,
        headers=response_headers if response_headers else None,
    )


class OptimizedJSONEncoder:
    """
    Optimized JSON encoder with performance improvements.
    """

    @staticmethod
    def encode(obj: Any) -> str:
        """
        Encode object to JSON string with optimizations.

        Args:
            obj: Object to encode

        Returns:
            JSON string
        """
        if ORJSON_AVAILABLE and orjson is not None:
            return orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS).decode("utf-8")
        else:
            return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def encode_bytes(obj: Any) -> bytes:
        """
        Encode object to JSON bytes with optimizations.

        Args:
            obj: Object to encode

        Returns:
            JSON bytes
        """
        if ORJSON_AVAILABLE and orjson is not None:
            return orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS)
        else:
            return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )


# Utility function to get performance stats
def get_json_performance_info() -> dict:
    """
    Get information about JSON serialization performance setup.

    Returns:
        Dictionary with performance information
    """
    return {
        "orjson_available": ORJSON_AVAILABLE,
        "serializer": "orjson" if ORJSON_AVAILABLE else "standard_json",
        "performance_level": "high" if ORJSON_AVAILABLE else "standard",
    }
