"""API v1 master router — registers all endpoint sub-routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    ai,
    auth,
    bookmarks,
    categories,
    contact,
    faqs,
    health,
    intelligence,
    ministries,
    notifications,
    schemes,
    search,
    services,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ai.router)
api_router.include_router(services.router)
api_router.include_router(schemes.router)
api_router.include_router(categories.router)
api_router.include_router(ministries.router)
api_router.include_router(faqs.router)
api_router.include_router(search.router)
api_router.include_router(intelligence.router)
api_router.include_router(contact.router)
api_router.include_router(bookmarks.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
