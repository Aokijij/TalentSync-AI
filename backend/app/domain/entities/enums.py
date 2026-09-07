from enum import StrEnum


class UserRole(StrEnum):
    CANDIDATE = "candidate"
    COMPANY = "company"
    ADMIN = "admin"


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    SEEN = "seen"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    TECHNICAL_INTERVIEW = "technical_interview"
    PSYCHOMETRIC_TEST = "psychometric_test"
    ACCEPTED = "accepted"
    HIRED = "hired"
    REJECTED = "rejected"
