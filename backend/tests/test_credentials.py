from types import SimpleNamespace as Row

import pytest
from pydantic import ValidationError

from app.api.schemas.credentials import CredentialRequirements, DrivingLicense
from app.api.schemas.profile import ProfileUpdate
from app.domain.services.credentials import (
    credential_evaluation,
    same_profession,
)


@pytest.mark.parametrize("legacy", [{}, {"status": "expired", "expires_on": "2020-01-01"}, {"status": "unknown"}])
def test_retired_dates_and_status_do_not_change_document_registration(legacy):
    profile = Row(driving_licenses=[{"category": "B1", **legacy}])
    job = Row(quality_details={"credential_requirements": {"driving_categories": ["B1"]}})
    assert credential_evaluation(profile, job)["status"] == "recorded"
    dumped = DrivingLicense(category="B1", **legacy).model_dump(mode="json")
    assert dumped == {"category": "B1"}


def test_alternative_categories_and_both_document_groups():
    job = Row(
        quality_details={
            "credential_requirements": {
                "driving_categories": ["B1", "C1"],
                "professional_cards": ["Ingeniería civil", "Arquitectura"],
            }
        }
    )
    profile = Row(
        driving_licenses=[
            {"category": "C1", "status": "valid", "expires_on": "2099-01-01"}
        ],
        professional_cards=[],
    )
    result = credential_evaluation(profile, job)
    assert result["status"] == "not_met" and result["groups"][0]["status"] == "recorded"
    profile.professional_cards = [
        {"profession": "Ingeniero civil", "status": "valid", "number": "PRIVATE-CARD"}
    ]
    result = credential_evaluation(profile, job)
    assert result["status"] == "recorded"
    assert "PRIVATE-CARD" not in str(result)
    assert not same_profession("Ingeniería de software", "Ingeniería de sistemas")
    assert not same_profession("Técnico en sistemas", "Ingeniería de sistemas")
    assert (
        credential_evaluation(profile, Row(quality_details={}))["status"]
        == "not_required"
    )


def test_schema_rejects_invalid_categories_dates_and_duplicates():
    with pytest.raises(ValidationError):
        DrivingLicense(category="D1")
    with pytest.raises(ValidationError):
        DrivingLicense(category="B1", expires_on="2026-30-40")
    with pytest.raises(ValidationError):
        ProfileUpdate(driving_licenses=[{"category": "B1"}, {"category": "B1"}])
    assert CredentialRequirements(
        driving_categories=["B1", "B1"]
    ).driving_categories == ["B1"]
