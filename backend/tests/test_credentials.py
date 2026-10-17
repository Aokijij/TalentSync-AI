from datetime import date
from types import SimpleNamespace as Row

import pytest
from pydantic import ValidationError

from app.api.schemas.credentials import CredentialRequirements, DrivingLicense
from app.api.schemas.profile import ProfileUpdate
from app.domain.services.credentials import (
    credential_evaluation,
    same_profession,
    validity,
)


@pytest.mark.parametrize(
    "record,driving,expected",
    [
        ({"status": "valid", "expires_on": "2030-01-01"}, True, "declared"),
        ({"status": "valid", "expires_on": "2020-01-01"}, True, "not_met"),
        ({"status": "valid", "expires_on": "2026-10-16"}, True, "declared"),
        ({"status": "valid"}, True, "review"),
        ({"status": "valid"}, False, "declared"),
        ({"status": "unknown", "expires_on": "2030-01-01"}, True, "review"),
        ({"status": "suspended", "expires_on": "2030-01-01"}, False, "not_met"),
        ({"status": "in_progress"}, False, "not_met"),
    ],
)
def test_validity_is_separate_from_official_verification(record, driving, expected):
    assert validity(record, driving=driving, today=date(2026, 10, 16)) == expected


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
    assert result["status"] == "not_met" and result["groups"][0]["status"] == "declared"
    profile.professional_cards = [
        {"profession": "Ingeniero civil", "status": "valid", "number": "PRIVATE-CARD"}
    ]
    result = credential_evaluation(profile, job)
    assert result["status"] == "declared"
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
