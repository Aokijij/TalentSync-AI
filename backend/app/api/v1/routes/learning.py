from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr

from app.api.deps import (
    get_curated_catalog,
    get_learn_catalog,
    get_public_learning_catalog,
    get_text_analysis,
    get_unit_of_work,
    get_youtube_learning,
    require_roles,
)
from app.api.schemas.learning import (
    ExternalCertificate,
    ResourceContent,
    ResourceImport,
    ResourceUpdate,
)
from app.application.use_cases import learning as cases
from app.application.use_cases import learning_resources, learning_sources
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)
admin = require_roles(UserRole.ADMIN)


class LearnPreview(BaseModel):
    kind: Literal["modules", "learning-paths"] = "modules"
    products: str = Field(default="", max_length=120, pattern=r"^[a-z0-9,-]*$")
    cursor: str = Field(default="", max_length=4000)


class LearnImport(BaseModel):
    preview_id: str = Field(min_length=20, max_length=100)
    ids: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(min_length=1, max_length=100)


class CuratedImport(BaseModel):
    revision: str = Field(min_length=24, max_length=24)
    ids: list[Annotated[str, Field(min_length=1, max_length=160)]] = Field(min_length=1, max_length=50)
    publish: bool = False


class PublicPreview(BaseModel):
    query: str = Field(min_length=3, max_length=80)
    refresh: bool = False


class PublicImport(LearnImport):
    ids: list[Annotated[str, Field(min_length=1, max_length=160)]] = Field(min_length=1, max_length=20)
    publish: bool = False


class PublicRefresh(BaseModel):
    provider: Literal["sena", "sapiencia"]


class YouTubePreview(BaseModel):
    url: str = Field(min_length=10, max_length=1000)


class YouTubeImport(BaseModel):
    preview_id: str = Field(min_length=20, max_length=100)
    editorial: ResourceContent
    publish: bool = False


@router.get("/admin/learning/sources/youtube")
def youtube_status(user=Depends(admin), gateway=Depends(get_youtube_learning)):
    return gateway.status()


@router.post("/admin/learning/sources/youtube/preview")
def youtube_preview(payload: YouTubePreview, user=Depends(admin), gateway=Depends(get_youtube_learning)):
    return gateway.preview(payload.url, actor_id=user.id)


@router.post("/admin/learning/sources/youtube/import")
def youtube_import(payload: YouTubeImport, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_youtube_learning)):
    identifier = gateway.selected(payload.preview_id, actor_id=user.id)
    content = payload.editorial.model_dump(mode="json")
    # Independent editorial fields are supplied by the reviewer; API descriptions,
    # channel names, statistics and sample titles are not copied into persistence.
    content.update(url=f"https://www.youtube.com/playlist?list={identifier}", provider="YouTube · selección de TalentSync",
                   cost="free", sponsored=False, affiliate=False, disclosure="")
    content.setdefault("details", None)
    content["details"] = {**(content["details"] or {}), "certificate_cost": "none",
                          "certificate_notes": "Esta lista de reproducción no concede un certificado de TalentSync. Consulta al creador si ofrece una formación certificada independiente."}
    selected = [{"source_id": identifier, "content": content,
                 "source": {"provider": "youtube", "id": identifier, "mode": "editorial", "api_metadata_stored": False,
                            "reviewed_at": datetime.now(timezone.utc).date().isoformat()}}]
    return learning_resources.import_source(db, user, selected, namespace="youtube", publish=payload.publish)


@router.post("/admin/learning/sources/sena/preview")
def preview_sena(payload: PublicPreview, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_public_learning_catalog)):
    return learning_sources.preview_sena(db, user, gateway, payload.query, force=payload.refresh)


@router.post("/admin/learning/sources/sena/import")
def import_sena(payload: PublicImport, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_public_learning_catalog)):
    selected = gateway.selected(payload.preview_id, payload.ids, user.id)
    return learning_resources.import_source(db, user, selected, namespace="sena", publish=payload.publish)


@router.post("/admin/learning/sources/public/refresh")
def refresh_public(payload: PublicRefresh, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_public_learning_catalog)):
    if payload.provider == "sapiencia":
        return learning_sources.refresh_sapiencia(db, user, gateway, force=True)
    return learning_sources.refresh_sena(db, user, gateway, limit=5)


@router.get("/learning/opportunities")
def local_opportunities(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return learning_sources.opportunities(db)


@router.get("/admin/learning/sources/public")
def public_sources(user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_sources.opportunities(db)


@router.get("/admin/learning/sources/curated")
def curated_catalog(user=Depends(admin), gateway=Depends(get_curated_catalog)):
    return gateway.catalog()


@router.post("/admin/learning/sources/curated/import")
def import_curated(payload: CuratedImport, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_curated_catalog)):
    return learning_resources.import_source(db, user, gateway.selected(payload.revision, payload.ids),
                                            namespace="curated", publish=payload.publish)


@router.get("/admin/learning/sources")
def configured_learning_sources(user=Depends(admin), gateway=Depends(get_learn_catalog)):
    return {"microsoft_learn": {"configured": gateway.configured, "authentication": "Microsoft Entra",
                               "certificate_verification": False}}


@router.post("/admin/learning/sources/microsoft-learn/preview")
def preview_learn(payload: LearnPreview, user=Depends(admin), gateway=Depends(get_learn_catalog)):
    return gateway.preview(**payload.model_dump(), actor_id=user.id)


@router.post("/admin/learning/sources/microsoft-learn/import")
def import_learn(payload: LearnImport, user=Depends(admin), db=Depends(get_unit_of_work), gateway=Depends(get_learn_catalog)):
    selected = gateway.selected(payload.preview_id, payload.ids, actor_id=user.id)
    return learning_resources.import_source(db, user, selected)


class PlanUpdate(BaseModel):
    status: Literal["in_progress", "completed"] = "in_progress"


Answer = StrictInt | StrictFloat | Annotated[StrictStr, Field(max_length=100)] | Annotated[list[StrictInt], Field(max_length=10)]


class Submission(BaseModel):
    answers: dict[str, Answer] = Field(max_length=30)


class JourneyUpdate(BaseModel):
    version: StrictInt = Field(ge=1)
    answers: dict[str, Annotated[str, Field(max_length=550)]] = Field(default_factory=dict, max_length=3)
    activity_answers: dict[str, Answer] | None = Field(default=None, max_length=3)
    finish: bool = False
    add_to_profile: bool = False


@router.get("/learning/catalog")
def catalog(area: str = "recommended", user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.catalog(db, user, area)


@router.get("/admin/learning/resources")
def admin_resources(user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user)


@router.post("/admin/learning/resources", status_code=201)
def create_resource(payload: ResourceContent, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [payload.model_dump(mode="json")])


@router.post("/admin/learning/resources/import", status_code=201)
def import_resources(payload: ResourceImport, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [row.model_dump(mode="json") for row in payload.resources])


@router.put("/admin/learning/resources/{resource_id}")
def edit_resource(resource_id: str, payload: ResourceUpdate, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [payload.model_dump(mode="json", exclude={"version"})], resource_id, payload.version)


@router.get("/learning/jobs/{job_id}")
def opportunities(job_id: int, user=Depends(candidate), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.opportunities(db, user, job_id, nlp)


@router.get("/learning/plans")
def plans(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.plans(db, user)


@router.put("/learning/plans/{resource_id}")
def update_plan(resource_id: str, payload: PlanUpdate, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.plans(db, user, resource_id, payload.status)


@router.post("/learning/assessments/{assessment_id}/start")
def start(assessment_id: str, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.start_assessment(db, user, assessment_id)


@router.patch("/learning/plans/{resource_id}/journey")
def save_journey(resource_id: str, payload: JourneyUpdate, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.save_journey(db, user, resource_id, payload.model_dump())


@router.post("/learning/attempts/{attempt_id}/submit")
def submit(attempt_id: str, payload: Submission, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.submit_assessment(db, user, attempt_id, payload.answers)


@router.get("/learning/passport")
def passport(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.passport(db, user)


@router.get("/learning/patterns")
def patterns(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.patterns(db, user)


@router.delete("/learning/plans/{resource_id}")
def leave_plan(resource_id: str, version: int, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.leave_plan(db, user, resource_id, version)


@router.post("/learning/plans/{resource_id}/certificate")
def certificate(resource_id: str, payload: ExternalCertificate, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.register_external_certificate(db, user, resource_id, payload.model_dump())
