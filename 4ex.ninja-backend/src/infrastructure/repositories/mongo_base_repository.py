"""
Base MongoDB Repository Implementation - Concrete implementation of IBaseRepository

This module provides the base MongoDB repository implementation that all
entity-specific repositories inherit from, implementing common CRUD operations
with integrated performance monitoring and caching.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, Generic, Sequence, Union
from contextlib import asynccontextmanager
from datetime import datetime
from abc import ABC
import logging
import time

try:
    from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase  # type: ignore
    from pymongo import ASCENDING, DESCENDING  # type: ignore
    from pymongo.errors import PyMongoError  # type: ignore
    from bson import ObjectId  # type: ignore

    MOTOR_AVAILABLE = True
except ImportError:
    # Fallback for when motor is not installed
    AsyncIOMotorCollection = None
    AsyncIOMotorDatabase = None
    ASCENDING = 1
    DESCENDING = -1
    PyMongoError = Exception
    ObjectId = None
    MOTOR_AVAILABLE = False

from ...core.interfaces.repository import IBaseRepository, RepositoryError

# Performance monitoring imports
try:
    from ..performance_manager import get_performance_manager

    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

# Generic type for entities
T = TypeVar("T")

logger = logging.getLogger(__name__)


class MongoBaseRepository(IBaseRepository[T], ABC, Generic[T]):
    """
    Base MongoDB repository implementation.

    Provides concrete implementation of common CRUD operations for MongoDB,
    following the Repository pattern defined in the core interfaces.
    """

    def __init__(
        self,
        database: Any,
        collection_name: str,
        entity_class: Type[T],
        session: Optional[Any] = None,
    ):
        """
        Initialize the repository.

        Args:
            database: MongoDB database instance
            collection_name: Name of the MongoDB collection
            entity_class: The entity class this repository manages
            session: Optional MongoDB session for transactions
        """
        self._database = database
        self._collection: Any = database[collection_name]
        self._entity_class = entity_class
        self._collection_name = collection_name
        self._session = session  # MongoDB session for transactions

        # Performance monitoring
        self._performance_manager = (
            get_performance_manager() if PERFORMANCE_MONITORING_AVAILABLE else None
        )

    def _record_query_performance(
        self,
        operation: str,
        query_filter: Dict[str, Any],
        execution_time_ms: float,
        result_count: int = 0,
    ):
        """Record query performance metrics."""
        try:
            if self._performance_manager and self._performance_manager.query_monitor:
                self._performance_manager.query_monitor.record_query(
                    query_type=operation,
                    collection=self._collection_name,
                    duration_ms=execution_time_ms,
                    success=True,
                    result_count=result_count,
                    query_filter=query_filter,
                )

            # Also record for optimization analysis
            if self._performance_manager:
                self._performance_manager.record_query_for_optimization(
                    collection=self._collection_name,
                    operation=operation,
                    query_filter=query_filter,
                    execution_time_ms=execution_time_ms,
                    result_count=result_count,
                )
        except Exception as e:
            logger.debug(f"Error recording performance metrics: {e}")

    def _record_query_error(
        self,
        operation: str,
        query_filter: Dict[str, Any],
        execution_time_ms: float,
        error: str,
    ):
        """Record query error metrics."""
        try:
            if self._performance_manager and self._performance_manager.query_monitor:
                self._performance_manager.query_monitor.record_query(
                    query_type=operation,
                    collection=self._collection_name,
                    duration_ms=execution_time_ms,
                    success=False,
                    result_count=0,
                    query_filter=query_filter,
                    error=error,
                )
        except Exception as e:
            logger.debug(f"Error recording error metrics: {e}")

    async def _get_from_cache(
        self, cache_key: str, namespace: str = "repository"
    ) -> Optional[Any]:
        """Get data from cache if available."""
        try:
            if self._performance_manager and self._performance_manager.cache_manager:
                return await self._performance_manager.cache_manager.get(
                    namespace=namespace, identifier=cache_key
                )
        except Exception as e:
            logger.debug(f"Error getting from cache: {e}")
        return None

    async def _set_cache(
        self,
        cache_key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        namespace: str = "repository",
    ):
        """Set data in cache if available."""
        try:
            if self._performance_manager and self._performance_manager.cache_manager:
                await self._performance_manager.cache_manager.set(
                    namespace=namespace,
                    identifier=cache_key,
                    value=value,
                    ttl_seconds=ttl_seconds,
                )
        except Exception as e:
            logger.debug(f"Error setting cache: {e}")

    def _entity_to_dict(self, entity: T) -> dict:
        """
        Convert entity to dictionary for MongoDB storage.

        Args:
            entity: The entity to convert

        Returns:
            Dictionary representation of the entity
        """
        if hasattr(entity, "to_dict") and callable(getattr(entity, "to_dict")):
            return entity.to_dict()  # type: ignore
        elif hasattr(entity, "__dict__"):
            # Convert dataclass or simple object to dict
            data = {}
            for key, value in entity.__dict__.items():
                if isinstance(value, datetime):
                    data[key] = value
                elif hasattr(value, "value"):  # Handle enums
                    data[key] = value.value
                else:
                    data[key] = value
            return data
        else:
            raise RepositoryError(f"Cannot convert {type(entity)} to dictionary")

    def _dict_to_entity(self, data: Optional[dict]) -> Optional[T]:
        """
        Convert dictionary from MongoDB to entity.

        Args:
            data: Dictionary from MongoDB

        Returns:
            Entity instance or None if data is None
        """
        if data is None:
            return None

        # Remove MongoDB's _id field if present and not needed
        if "_id" in data and not hasattr(self._entity_class, "_id"):
            data.pop("_id")

        # Handle datetime conversion if needed
        for key, value in data.items():
            if isinstance(value, str) and key.endswith("_at"):
                try:
                    data[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass  # Keep as string if not a valid datetime

        try:
            return self._entity_class(**data)
        except Exception as e:
            raise RepositoryError(
                f"Failed to create entity from data: {data}", original_error=e
            )

    async def create(self, entity: T) -> T:
        """Create a new entity in MongoDB with performance monitoring."""
        start_time = time.time()
        data = {}

        try:
            data = self._entity_to_dict(entity)

            # Add created timestamp if not present
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()

            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()

            result = await self._collection.insert_one(
                data, **self._get_session_kwargs()
            )

            # Add the generated ID to the data
            data["_id"] = result.inserted_id

            # Record performance metrics
            execution_time_ms = (time.time() - start_time) * 1000
            self._record_query_performance(
                operation="insert",
                query_filter={"operation": "insert"},
                execution_time_ms=execution_time_ms,
                result_count=1,
            )

            logger.info(
                f"Created entity in {self._collection_name}: {result.inserted_id}"
            )
            created_entity = self._dict_to_entity(data)
            if created_entity is None:
                raise RepositoryError(
                    f"Failed to create entity in {self._collection_name}: entity conversion returned None"
                )
            return created_entity

        except PyMongoError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._record_query_error(
                operation="insert",
                query_filter={"operation": "insert"},
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
            raise RepositoryError(
                f"Failed to create entity in {self._collection_name}", original_error=e
            )

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Retrieve an entity by its unique identifier with caching and performance monitoring."""
        start_time = time.time()

        # Check cache first
        cache_key = f"get_by_id:{entity_id}"
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for entity {entity_id} in {self._collection_name}")
            return cached_result

        try:
            # Handle ObjectId conversion if available
            query_filters = []

            # Add string ID lookup
            query_filters.append({"id": entity_id})

            # Add ObjectId lookup if ObjectId is available and entity_id is valid ObjectId
            if ObjectId and self._is_valid_object_id(entity_id):
                query_filters.append({"_id": ObjectId(entity_id)})
            else:
                # Fallback to string _id lookup
                query_filters.append({"_id": entity_id})

            # Add entity-specific ID fields
            if hasattr(self._entity_class, "signal_id"):
                query_filters.append({"signal_id": entity_id})
            if hasattr(self._entity_class, "strategy_id"):
                query_filters.append({"strategy_id": entity_id})

            query = {"$or": query_filters}
            data = await self._collection.find_one(query, **self._get_session_kwargs())

            # Record performance metrics
            execution_time_ms = (time.time() - start_time) * 1000
            result_count = 1 if data else 0
            self._record_query_performance(
                operation="find",
                query_filter=query,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
            )

            result = self._dict_to_entity(data) if data else None

            # Cache the result if found
            if result is not None:
                await self._set_cache(
                    cache_key, result, ttl_seconds=300
                )  # 5 minute cache

            return result

        except PyMongoError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self._record_query_error(
                operation="find",
                query_filter=query,
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
            raise RepositoryError(
                f"Failed to get entity by ID {entity_id}", original_error=e
            )

    def _is_valid_object_id(self, id_string: str) -> bool:
        """Check if string is a valid ObjectId."""
        if not ObjectId:
            return False
        try:
            ObjectId(id_string)
            return True
        except:
            return False

    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[T]:
        """Retrieve all entities with optional pagination."""
        try:
            cursor = self._collection.find({}, **self._get_session_kwargs())

            if offset:
                cursor = cursor.skip(offset)
            if limit:
                cursor = cursor.limit(limit)

            # Sort by created_at desc by default
            cursor = cursor.sort("created_at", DESCENDING)

            entities = []
            async for data in cursor:
                entity = self._dict_to_entity(data)
                if entity is not None:
                    entities.append(entity)

            return entities

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to get all entities from {self._collection_name}",
                original_error=e,
            )

    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            data = self._entity_to_dict(entity)

            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()

            # Extract ID for query
            entity_id = (
                data.get("id") or data.get("signal_id") or data.get("strategy_id")
            )
            if not entity_id:
                raise RepositoryError("Entity must have an ID for update")

            query = {"$or": [{"_id": entity_id}, {"id": entity_id}]}
            if "signal_id" in data:
                query["$or"].append({"signal_id": entity_id})
            if "strategy_id" in data:
                query["$or"].append({"strategy_id": entity_id})

            result = await self._collection.replace_one(query, data)

            if result.matched_count == 0:
                raise RepositoryError(
                    f"Entity with ID {entity_id} not found for update"
                )

            logger.info(f"Updated entity in {self._collection_name}: {entity_id}")
            updated_entity = self._dict_to_entity(data)
            if updated_entity is None:
                raise RepositoryError(
                    f"Failed to update entity in {self._collection_name}: entity conversion returned None"
                )
            return updated_entity

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to update entity in {self._collection_name}", original_error=e
            )

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by its unique identifier."""
        try:
            query = {"$or": [{"_id": entity_id}, {"id": entity_id}]}
            if hasattr(self._entity_class, "signal_id"):
                query["$or"].append({"signal_id": entity_id})
            if hasattr(self._entity_class, "strategy_id"):
                query["$or"].append({"strategy_id": entity_id})

            result = await self._collection.delete_one(
                query, **self._get_session_kwargs()
            )

            if result.deleted_count > 0:
                logger.info(f"Deleted entity from {self._collection_name}: {entity_id}")
                return True
            return False

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to delete entity {entity_id}", original_error=e
            )

    async def exists(self, entity_id: str) -> bool:
        """Check if an entity exists."""
        try:
            query = {"$or": [{"_id": entity_id}, {"id": entity_id}]}
            if hasattr(self._entity_class, "signal_id"):
                query["$or"].append({"signal_id": entity_id})
            if hasattr(self._entity_class, "strategy_id"):
                query["$or"].append({"strategy_id": entity_id})

            count = await self._collection.count_documents(query, limit=1)
            return count > 0

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to check existence of entity {entity_id}", original_error=e
            )

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching optional filters."""
        try:
            query = self._build_query(filters) if filters else {}
            return await self._collection.count_documents(query)

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to count entities in {self._collection_name}", original_error=e
            )

    async def find_by_criteria(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[T]:
        """Find entities matching specific criteria."""
        try:
            query = self._build_query(filters)
            cursor = self._collection.find(query, **self._get_session_kwargs())

            if offset:
                cursor = cursor.skip(offset)
            if limit:
                cursor = cursor.limit(limit)

            if sort_by:
                sort_direction = (
                    ASCENDING if sort_order.lower() == "asc" else DESCENDING
                )
                cursor = cursor.sort(sort_by, sort_direction)
            else:
                cursor = cursor.sort("created_at", DESCENDING)

            entities = []
            async for data in cursor:
                entity = self._dict_to_entity(data)
                if entity is not None:
                    entities.append(entity)

            return entities

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to find entities by criteria in {self._collection_name}",
                original_error=e,
            )

    async def find_by_date_range(
        self,
        date_field: str,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
    ) -> List[T]:
        """Find entities within a date range."""
        try:
            query = {date_field: {"$gte": start_date, "$lte": end_date}}

            cursor = self._collection.find(query, **self._get_session_kwargs()).sort(
                date_field, DESCENDING
            )

            if limit:
                cursor = cursor.limit(limit)

            entities = []
            async for data in cursor:
                entity = self._dict_to_entity(data)
                if entity is not None:
                    entities.append(entity)

            return entities

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to find entities by date range in {self._collection_name}",
                original_error=e,
            )

    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in a single operation."""
        try:
            if not entities:
                return []

            documents = []
            for entity in entities:
                data = self._entity_to_dict(entity)
                if "created_at" not in data:
                    data["created_at"] = datetime.utcnow()
                data["updated_at"] = datetime.utcnow()
                documents.append(data)

            result = await self._collection.insert_many(
                documents, **self._get_session_kwargs()
            )

            # Add generated IDs back to documents
            for i, inserted_id in enumerate(result.inserted_ids):
                documents[i]["_id"] = inserted_id

            logger.info(
                f"Bulk created {len(entities)} entities in {self._collection_name}"
            )

            # Convert documents back to entities, filtering out None values
            created_entities = []
            for doc in documents:
                entity = self._dict_to_entity(doc)
                if entity is not None:
                    created_entities.append(entity)

            if len(created_entities) != len(documents):
                raise RepositoryError(
                    f"Failed to create some entities in {self._collection_name}: conversion returned None for some entities"
                )

            return created_entities

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to bulk create entities in {self._collection_name}",
                original_error=e,
            )

    async def bulk_update(self, entities: List[T]) -> List[T]:
        """Update multiple entities in a single operation."""
        try:
            if not entities:
                return []

            operations = []
            updated_entities = []

            for entity in entities:
                data = self._entity_to_dict(entity)
                data["updated_at"] = datetime.utcnow()

                entity_id = (
                    data.get("id") or data.get("signal_id") or data.get("strategy_id")
                )
                if not entity_id:
                    continue

                query = {"$or": [{"_id": entity_id}, {"id": entity_id}]}
                if "signal_id" in data:
                    query["$or"].append({"signal_id": entity_id})
                if "strategy_id" in data:
                    query["$or"].append({"strategy_id": entity_id})

                operations.append(
                    {"update_one": {"filter": query, "update": {"$set": data}}}
                )
                entity = self._dict_to_entity(data)
                if entity is not None:
                    updated_entities.append(entity)

            if operations:
                await self._collection.bulk_write(
                    operations, **self._get_session_kwargs()
                )
                logger.info(
                    f"Bulk updated {len(operations)} entities in {self._collection_name}"
                )

            return updated_entities

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to bulk update entities in {self._collection_name}",
                original_error=e,
            )

    async def bulk_delete(self, entity_ids: List[str]) -> int:
        """Delete multiple entities in a single operation."""
        try:
            if not entity_ids:
                return 0

            query = {"$or": []}
            for entity_id in entity_ids:
                id_query = {"$or": [{"_id": entity_id}, {"id": entity_id}]}
                if hasattr(self._entity_class, "signal_id"):
                    id_query["$or"].append({"signal_id": entity_id})
                if hasattr(self._entity_class, "strategy_id"):
                    id_query["$or"].append({"strategy_id": entity_id})
                query["$or"].append(id_query)

            result = await self._collection.delete_many(
                query, **self._get_session_kwargs()
            )

            logger.info(
                f"Bulk deleted {result.deleted_count} entities from {self._collection_name}"
            )
            return result.deleted_count

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to bulk delete entities in {self._collection_name}",
                original_error=e,
            )

    def _build_query(self, filters: Dict[str, Any]) -> dict:
        """
        Build MongoDB query from filters.

        Args:
            filters: Dictionary of field-value pairs

        Returns:
            MongoDB query dictionary
        """
        query = {}

        for key, value in filters.items():
            if value is None:
                continue

            # Handle enum values
            if hasattr(value, "value"):
                query[key] = value.value
            # Handle list values (IN query)
            elif isinstance(value, list):
                query[key] = {"$in": value}
            # Handle datetime ranges
            elif isinstance(value, dict) and any(
                k in value for k in ["gte", "lte", "gt", "lt"]
            ):
                range_query = {}
                if "gte" in value:
                    range_query["$gte"] = value["gte"]
                if "lte" in value:
                    range_query["$lte"] = value["lte"]
                if "gt" in value:
                    range_query["$gt"] = value["gt"]
                if "lt" in value:
                    range_query["$lt"] = value["lt"]
                query[key] = range_query
            else:
                query[key] = value

        return query

    async def get_by_ids(self, entity_ids: List[str]) -> List[T]:
        """
        Retrieve multiple entities by their IDs.

        Args:
            entity_ids: List of entity IDs to retrieve

        Returns:
            List of found entities
        """
        try:
            if not entity_ids:
                return []

            query_filters = []
            for entity_id in entity_ids:
                filters: List[Dict[str, Any]] = [{"id": entity_id}]

                if ObjectId and self._is_valid_object_id(entity_id):
                    filters.append({"_id": ObjectId(entity_id)})
                else:
                    filters.append({"_id": entity_id})

                if hasattr(self._entity_class, "signal_id"):
                    filters.append({"signal_id": entity_id})
                if hasattr(self._entity_class, "strategy_id"):
                    filters.append({"strategy_id": entity_id})

                query_filters.append({"$or": filters})

            query = {"$or": query_filters}
            cursor = self._collection.find(query, **self._get_session_kwargs())

            entities = []
            async for data in cursor:
                entity = self._dict_to_entity(data)
                if entity is not None:
                    entities.append(entity)

            return entities

        except PyMongoError as e:
            raise RepositoryError(f"Failed to get entities by IDs", original_error=e)

    async def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        """
        Find a single entity matching the given filters.

        Args:
            filters: Dictionary of field-value pairs to filter by

        Returns:
            First matching entity or None if not found
        """
        try:
            query = self._build_query(filters)
            data = await self._collection.find_one(query, **self._get_session_kwargs())
            return self._dict_to_entity(data) if data else None

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to find entity by criteria in {self._collection_name}",
                original_error=e,
            )

    async def upsert(self, entity: T, update_fields: Optional[List[str]] = None) -> T:
        """
        Insert or update an entity.

        Args:
            entity: Entity to upsert
            update_fields: Specific fields to update (if None, update all fields)

        Returns:
            The upserted entity
        """
        try:
            data = self._entity_to_dict(entity)
            entity_id = (
                data.get("id") or data.get("signal_id") or data.get("strategy_id")
            )

            if not entity_id:
                # No ID provided, perform insert
                return await self.create(entity)

            # Build query for existing entity
            query = {"$or": [{"id": entity_id}]}
            if ObjectId and self._is_valid_object_id(entity_id):
                query["$or"].append({"_id": ObjectId(entity_id)})
            else:
                query["$or"].append({"_id": entity_id})

            if "signal_id" in data:
                query["$or"].append({"signal_id": entity_id})
            if "strategy_id" in data:
                query["$or"].append({"strategy_id": entity_id})

            # Prepare update data
            update_data = data.copy()
            if update_fields:
                # Only update specified fields
                update_data = {
                    field: data[field] for field in update_fields if field in data
                }

            # Add/update timestamps
            update_data["updated_at"] = datetime.utcnow()
            if "created_at" not in update_data:
                update_data["created_at"] = datetime.utcnow()

            result = await self._collection.update_one(
                query, {"$set": update_data}, upsert=True, **self._get_session_kwargs()
            )

            if result.upserted_id:
                update_data["_id"] = result.upserted_id
                logger.info(
                    f"Upserted (inserted) entity in {self._collection_name}: {entity_id}"
                )
            else:
                logger.info(
                    f"Upserted (updated) entity in {self._collection_name}: {entity_id}"
                )

            upserted_entity = self._dict_to_entity(update_data)
            if upserted_entity is None:
                raise RepositoryError(
                    f"Failed to upsert entity in {self._collection_name}: entity conversion returned None"
                )
            return upserted_entity

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to upsert entity in {self._collection_name}", original_error=e
            )

    async def delete_by_criteria(self, filters: Dict[str, Any]) -> int:
        """
        Delete entities matching the given filters.

        Args:
            filters: Dictionary of field-value pairs to filter by

        Returns:
            Number of entities deleted
        """
        try:
            query = self._build_query(filters)
            result = await self._collection.delete_many(
                query, **self._get_session_kwargs()
            )

            logger.info(
                f"Deleted {result.deleted_count} entities from {self._collection_name}"
            )
            return result.deleted_count

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to delete entities by criteria in {self._collection_name}",
                original_error=e,
            )

    async def update_by_criteria(
        self, filters: Dict[str, Any], update_data: Dict[str, Any], upsert: bool = False
    ) -> int:
        """
        Update entities matching the given filters.

        Args:
            filters: Dictionary of field-value pairs to filter by
            update_data: Dictionary of fields to update
            upsert: Whether to insert if no documents match

        Returns:
            Number of entities updated
        """
        try:
            query = self._build_query(filters)

            # Add updated timestamp
            update_data_copy = update_data.copy()
            update_data_copy["updated_at"] = datetime.utcnow()

            result = await self._collection.update_many(
                query,
                {"$set": update_data_copy},
                upsert=upsert,
                **self._get_session_kwargs(),
            )

            count = result.modified_count + (1 if result.upserted_id else 0)
            logger.info(f"Updated {count} entities in {self._collection_name}")
            return count

        except PyMongoError as e:
            raise RepositoryError(
                f"Failed to update entities by criteria in {self._collection_name}",
                original_error=e,
            )

    def _get_session_kwargs(self) -> Dict[str, Any]:
        """
        Get session kwargs for MongoDB operations.

        Returns:
            Dictionary containing session if available
        """
        return {"session": self._session} if self._session else {}

    def set_session(self, session: Optional[Any]) -> None:
        """
        Set the MongoDB session for this repository.

        Args:
            session: MongoDB session for transaction support
        """
        self._session = session

    async def in_transaction(self) -> bool:
        """
        Check if repository is currently in a transaction.

        Returns:
            True if in transaction, False otherwise
        """
        return self._session is not None and getattr(
            self._session, "in_transaction", False
        )
