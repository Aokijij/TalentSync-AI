from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    applications,
    auth,
    companies,
    jobs,
    notifications,
    profiles,
    recommendations,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(
    applications.router, prefix="/applications", tags=["applications"]
)
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
