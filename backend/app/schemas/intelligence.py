"""Request schemas for the OneGov intelligence endpoints."""

from uuid import UUID

from pydantic import BaseModel, Field


class EligibilityCheckRequest(BaseModel):
    """User asks: am I eligible for this service/scheme, given my facts?"""

    entity_type: str = Field(..., pattern="^(service|scheme)$")
    entity_slug: str = Field(..., min_length=1, max_length=255)
    criteria: dict[str, object] = Field(default_factory=dict)


class TaskPlannerRequest(BaseModel):
    """Generate tasks for a citizen journey and/or specific services."""

    journey_slug: str | None = Field(default=None, max_length=150)
    service_slugs: list[str] = Field(default_factory=list, max_length=20)


class TaskUpdateRequest(BaseModel):
    """Update status/priority/notes of a user task."""

    status: str | None = Field(default=None, pattern="^(PENDING|IN_PROGRESS|COMPLETED|BLOCKED)$")
    priority: str | None = Field(default=None, pattern="^(HIGH|MEDIUM|LOW)$")
    notes: str | None = Field(default=None, max_length=2000)


class ReadinessRequest(BaseModel):
    entity_type: str = Field(..., pattern="^(service|scheme)$")
    entity_slug: str = Field(..., min_length=1, max_length=255)
    user_id: UUID | None = Field(default=None)


class NearbyQuery(BaseModel):
    q: str = ""
    state: str = ""
    city: str = ""