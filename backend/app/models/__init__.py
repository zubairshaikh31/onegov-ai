"""
Models package.
Import all models here so Alembic's autogenerate can discover them.
"""

from app.models.base import Base, BaseModel  # noqa: F401
from app.models.role import Permission, Role, RolePermission, UserRole  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.government import (  # noqa: F401
    ApplicationStep,
    Category,
    Department,
    FAQ,
    Keyword,
    KnowledgeChunk,
    Ministry,
    RequiredDocument,
    Scheme,
    Service,
    ServiceDocument,
    ServiceRelation,
)
from app.models.activity import (  # noqa: F401
    AIChatHistory,
    Analytics,
    AuditLog,
    Bookmark,
    ContactMessage,
    Feedback,
    GovernmentOffice,
    Notification,
    SearchHistory,
)
from app.models.intelligence import (  # noqa: F401
    CitizenJourney,
    EligibilityRule,
    JourneyStep,
    LifeEvent,
    SchemeRelation,
    ServiceVideo,
    SourceChangeLog,
    SourceMonitor,
    UserDocument,
    UserTask,
    Video,
)

__all__ = [
    "Base", "BaseModel", "Permission", "Role", "RolePermission", "UserRole",
    "User", "Ministry", "Department", "Category", "Service", "RequiredDocument",
    "ServiceDocument", "ApplicationStep", "Scheme", "FAQ", "Keyword",
    "ServiceRelation", "KnowledgeChunk", "Bookmark", "Notification", "SearchHistory",
    "AIChatHistory", "Feedback", "ContactMessage", "GovernmentOffice", "Analytics", "AuditLog",
    "Video", "ServiceVideo", "SourceMonitor", "SourceChangeLog", "EligibilityRule",
    "CitizenJourney", "JourneyStep", "LifeEvent", "UserTask", "UserDocument", "SchemeRelation",
]
