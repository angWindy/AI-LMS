"""
API v1 Router - aggregates all API endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, courses, lessons, assignments

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(lessons.router)
api_router.include_router(assignments.router)
