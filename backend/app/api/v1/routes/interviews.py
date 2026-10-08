import json
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field, model_validator

from app.api.deps import get_current_user, get_interview_ice, get_unit_of_work
from app.application.use_cases import interviews as cases
from app.core.limiter import limiter

router = APIRouter(prefix="/interviews")


class RoomCreate(BaseModel):
    application_id: int = Field(gt=0)
    title: str = Field(default="Entrevista técnica", min_length=3, max_length=150)


class Point(BaseModel):
    x: float = Field(ge=0, le=1000)
    y: float = Field(ge=0, le=600)


class Stroke(BaseModel):
    points: list[Point] = Field(min_length=1, max_length=100)


class Document(BaseModel):
    expected_version: int = Field(ge=1)
    code: str = Field(max_length=30000)
    whiteboard: list[Stroke] = Field(max_length=150)


class Presence(BaseModel):
    participant_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    after_id: int = Field(default=0, ge=0)


class Signal(BaseModel):
    recipient_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    kind: Literal["offer", "answer", "ice"]
    payload: dict

    @model_validator(mode="after")
    def bounded(self):
        if len(json.dumps(self.payload)) > (64000 if self.kind != "ice" else 4000):
            raise ValueError("Mensaje demasiado grande")
        if self.kind in {"offer", "answer"} and (self.payload.get("type") != self.kind or not isinstance(self.payload.get("sdp"), str)):
            raise ValueError("Descripción de conexión inválida")
        return self


@router.get("/rooms")
def rooms(user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.rooms(db, user)


@router.post("/rooms", status_code=201)
def create(payload: RoomCreate, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.create(db, user, payload.application_id, payload.title)


@router.get("/rooms/{room_id}")
def room(room_id: str, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.room_view(cases.get(db, user, room_id))


@router.get("/rooms/{room_id}/ice")
@limiter.limit("20/minute")
def connectivity(request: Request, response: Response, room_id: str, user=Depends(get_current_user),
                 db=Depends(get_unit_of_work), issuer=Depends(get_interview_ice)):
    result = cases.connectivity(db, user, room_id, issuer)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.put("/rooms/{room_id}")
def save(room_id: str, payload: Document, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.save(db, user, room_id, payload.model_dump())


@router.post("/rooms/{room_id}/close")
def close(room_id: str, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.close(db, user, room_id)


@router.post("/rooms/{room_id}/connect")
def connect(room_id: str, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.connect(db, user, room_id)


@router.post("/rooms/{room_id}/presence")
def presence(room_id: str, payload: Presence, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.poll(db, user, room_id, payload.participant_id, payload.after_id)


@router.post("/rooms/{room_id}/participants/{participant_id}/signal")
def signal(room_id: str, participant_id: str, payload: Signal, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.signal(db, user, room_id, participant_id, payload.model_dump())


@router.delete("/rooms/{room_id}/participants/{participant_id}")
def disconnect(room_id: str, participant_id: str, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.disconnect(db, user, room_id, participant_id)
