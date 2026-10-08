from fastapi import APIRouter

from app.api.v1.routes import (
    account,
    admin,
    applications,
    auth,
    companies,
    ecosystem,
    hiring,
    interviews,
    jobs,
    learning,
    match_settings,
    notifications,
    organizations,
    profiles,
    recommendations,
    workflow,
)

api_router = APIRouter()
api_router.include_router(account.router, tags=["account"])
api_router.include_router(organizations.router, tags=["organizations"])
api_router.include_router(match_settings.router, tags=["matching"])
api_router.include_router(workflow.router, tags=["workflow"])
api_router.include_router(learning.router, tags=["learning"])
api_router.include_router(hiring.router, tags=["hiring"])
api_router.include_router(interviews.router, tags=["interviews"])
api_router.include_router(ecosystem.router, tags=["ecosystem"])
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
