"""
Response optimization utilities for API endpoints.

This module provides utilities for optimizing API responses through:
- Field selection (allowing clients to specify which fields to include)
- Response filtering and transformation
- Pagination optimization
"""

from typing import Any, Dict, List, Optional, Set, Union
from fastapi import Query
import logging

logger = logging.getLogger(__name__)


def parse_fields_parameter(fields: Optional[str] = None) -> Optional[Set[str]]:
    """
    Parse the fields query parameter into a set of field names.

    Args:
        fields: Comma-separated list of field names (e.g., "id,name,price")

    Returns:
        Set of field names or None if no fields specified
    """
    if not fields:
        return None

    return {field.strip() for field in fields.split(",") if field.strip()}


def filter_response_fields(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    included_fields: Optional[Set[str]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Filter response data to include only specified fields.

    Args:
        data: Response data (dict or list of dicts)
        included_fields: Set of field names to include. If None, returns all fields.

    Returns:
        Filtered response data
    """
    if not included_fields:
        return data

    def filter_dict(item: Dict[str, Any]) -> Dict[str, Any]:
        """Filter a single dictionary."""
        return {key: value for key, value in item.items() if key in included_fields}

    if isinstance(data, list):
        return [filter_dict(item) for item in data]
    elif isinstance(data, dict):
        return filter_dict(data)
    else:
        return data


def optimize_response_size(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    max_items: Optional[int] = None,
    included_fields: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Optimize response size through field filtering and item limiting.

    Args:
        data: Response data
        max_items: Maximum number of items to return (for lists)
        included_fields: Set of field names to include

    Returns:
        Optimized response with metadata
    """
    if isinstance(data, list):
        original_count = len(data)

        # Apply item limit if specified
        if max_items and original_count > max_items:
            data = data[:max_items]
            truncated = True
        else:
            truncated = False

        # Apply field filtering
        filtered_data = filter_response_fields(data, included_fields)

        return {
            "data": filtered_data,
            "meta": {
                "count": len(filtered_data),
                "original_count": original_count,
                "truncated": truncated,
                "fields_filtered": included_fields is not None,
                "included_fields": list(included_fields) if included_fields else None,
            },
        }
    else:
        # Single item response
        filtered_data = filter_response_fields(data, included_fields)

        return {
            "data": filtered_data,
            "meta": {
                "fields_filtered": included_fields is not None,
                "included_fields": list(included_fields) if included_fields else None,
            },
        }


class FieldSelector:
    """Dependency class for field selection in FastAPI endpoints."""

    def __init__(
        self,
        fields: Optional[str] = Query(
            None,
            description="Comma-separated list of fields to include in response (e.g., 'id,name,price')",
            example="id,pair,signal_type,entry_price",
        ),
    ):
        self.fields = parse_fields_parameter(fields)

    def filter(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Filter response data using the selected fields."""
        return filter_response_fields(data, self.fields)


class PaginationOptimizer:
    """Optimized pagination with cursor-based support for better performance."""

    def __init__(
        self,
        limit: int = Query(
            50, ge=1, le=1000, description="Number of items to retrieve"
        ),
        offset: int = Query(
            0, ge=0, description="Number of items to skip (offset-based pagination)"
        ),
        cursor: Optional[str] = Query(
            None, description="Cursor for cursor-based pagination"
        ),
        include_total: bool = Query(
            False,
            description="Include total count in response (may impact performance)",
        ),
    ):
        self.limit = limit
        self.offset = offset
        self.cursor = cursor
        self.include_total = include_total

    def is_cursor_based(self) -> bool:
        """Check if cursor-based pagination is being used."""
        return self.cursor is not None

    def create_pagination_meta(
        self,
        items: List[Any],
        total_count: Optional[int] = None,
        next_cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create pagination metadata for response."""
        meta = {
            "limit": self.limit,
            "count": len(items),
            "has_more": len(items)
            == self.limit,  # Assumes we fetched limit+1 to check for more
        }

        if self.is_cursor_based():
            meta["pagination_type"] = "cursor"
            meta["cursor"] = self.cursor
            if next_cursor:
                meta["next_cursor"] = next_cursor
        else:
            meta["pagination_type"] = "offset"
            meta["offset"] = self.offset
            meta["next_offset"] = self.offset + len(items) if meta["has_more"] else None

        if self.include_total and total_count is not None:
            meta["total"] = total_count

        return meta


def create_optimized_response(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    field_selector: Optional[FieldSelector] = None,
    pagination: Optional[PaginationOptimizer] = None,
    additional_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an optimized API response with field selection and pagination.

    Args:
        data: Response data
        field_selector: Field selector for filtering response fields
        pagination: Pagination optimizer for metadata
        additional_meta: Additional metadata to include

    Returns:
        Optimized response dictionary
    """
    # Apply field filtering
    if field_selector:
        data = field_selector.filter(data)

    response = {"data": data}

    # Add pagination metadata
    if pagination and isinstance(data, list):
        response["meta"] = pagination.create_pagination_meta(data)
    else:
        response["meta"] = {}

    # Add additional metadata
    if additional_meta:
        response["meta"].update(additional_meta)

    # Add field filtering info to meta
    if field_selector and field_selector.fields:
        response["meta"]["field_selection"] = {
            "enabled": True,
            "included_fields": list(field_selector.fields),
        }

    return response
