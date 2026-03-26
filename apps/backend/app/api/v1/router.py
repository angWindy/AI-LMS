"""
API v1 Router - aggregates all API endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import auth

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)

# TODO: Add more routers as they are implemented
# api_router.include_router(users.router)
# api_router.include_router(courses.router)
# api_router.include_router(assignments.router)
