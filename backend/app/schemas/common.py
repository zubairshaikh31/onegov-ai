"""
Shared Pydantic schemas used across the entire API.
Every endpoint returns the ApiResponse envelope for consistency.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standardised API response envelope.
    Every endpoint wraps its payload in this shape.

    Success:  {"success": true,  "message": "...", "data": {...}, "errors": null}
    Failure:  {"success": false, "message": "...", "data": null,  "errors": [...]}
    """

    success: bool
    message: str
    data: T | None = None
    errors: list[dict[str, str]] | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "Success") -> "ApiResponse[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(
        cls,
        message: str = "An error occurred",
        errors: list[dict[str, str]] | None = None,
    ) -> "ApiResponse[None]":
        return cls(success=False, message=message, data=None, errors=errors)


class PaginationMeta(BaseModel):
    """Pagination metadata included in list responses."""

    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: list[T]
    meta: PaginationMeta


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @classmethod
    def build_meta(cls, total: int, page: int, page_size: int) -> PaginationMeta:
        total_pages = max(1, -(-total // page_size))  # ceiling division
        return PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class UUIDResponse(BaseModel):
    """Minimal response returning just an ID (e.g. after creating a resource)."""
    id: UUID
