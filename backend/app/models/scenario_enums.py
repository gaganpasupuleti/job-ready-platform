"""Deterministic scenario challenge enums."""

from enum import StrEnum


class ScenarioDomain(StrEnum):
    CLOUD = "cloud"
    DEVOPS = "devops"
    CYBERSECURITY = "cybersecurity"


class ScenarioType(StrEnum):
    ARCHITECTURE = "architecture"
    TROUBLESHOOTING = "troubleshooting"
    INCIDENT_RESPONSE = "incident_response"
    SECURITY_REVIEW = "security_review"
    DEPLOYMENT = "deployment"
    OBSERVABILITY = "observability"
    DECISION_TREE = "decision_tree"


class ScenarioProgressStatus(StrEnum):
    ATTEMPTED = "attempted"
    MASTERED = "mastered"
