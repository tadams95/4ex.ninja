"""
Base Repository Interface - Core interface for data access patterns

This module defines the base repository interface that all entity-specific
repositories must implement, following the Repository pattern and clean
architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime

# Generic type for entities
T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """
    Base repository interface defining common CRUD operations.

    This interface provides the contract that all repository implementations
    must follow, ensuring consistent data access patterns across the application.
    """

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create a new entity in the repository.

        Args:
            entity: The entity to create

        Returns:
            The created entity with any generated fields (like ID, timestamps)

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Retrieve an entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[T]:
        """
        Retrieve all entities with optional pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update an existing entity in the repository.

        Args:
            entity: The entity to update (must have valid ID)

        Returns:
            The updated entity

        Raises:
            RepositoryError: If update fails or entity not found
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to delete

        Returns:
            True if deletion successful, False if entity not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """
        Check if an entity exists by its unique identifier.

        Args:
            entity_id: The unique identifier to check

        Returns:
            True if entity exists, False otherwise

        Raises:
            RepositoryError: If check fails
        """
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching optional filters.

        Args:
            filters: Optional dictionary of field-value pairs to filter by

        Returns:
            Number of entities matching the criteria

        Raises:
            RepositoryError: If count operation fails
        """
        pass

    @abstractmethod
    async def find_by_criteria(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> List[T]:
        """
        Find entities matching specific criteria with sorting and pagination.

        Args:
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            sort_by: Field name to sort by
            sort_order: Sort order ("asc" or "desc")

        Returns:
            List of entities matching the criteria

        Raises:
            RepositoryError: If search fails
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        date_field: str,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
    ) -> List[T]:
        """
        Find entities within a specific date range.

        Args:
            date_field: The name of the date field to filter on
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)
            limit: Maximum number of entities to return

        Returns:
            List of entities within the date range

        Raises:
            RepositoryError: If search fails
        """
        pass

    @abstractmethod
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in a single operation.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities with generated fields

        Raises:
            RepositoryError: If bulk creation fails
        """
        pass

    @abstractmethod
    async def bulk_update(self, entities: List[T]) -> List[T]:
        """
        Update multiple entities in a single operation.

        Args:
            entities: List of entities to update

        Returns:
            List of updated entities

        Raises:
            RepositoryError: If bulk update fails
        """
        pass

    @abstractmethod
    async def bulk_delete(self, entity_ids: List[str]) -> int:
        """
        Delete multiple entities in a single operation.

        Args:
            entity_ids: List of entity IDs to delete

        Returns:
            Number of entities successfully deleted

        Raises:
            RepositoryError: If bulk deletion fails
        """
        pass


class RepositoryError(Exception):
    """
    Custom exception for repository operations.

    This exception should be raised when repository operations fail,
    providing a clear separation between domain and infrastructure errors.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message}. Original error: {str(self.original_error)}"
        return self.message
