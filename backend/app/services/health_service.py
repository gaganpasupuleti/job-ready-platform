from app.schemas.health import HealthResponse


class HealthService:
    SERVICE_NAME = "job-ready-platform-api"

    def get_health(self) -> HealthResponse:
        return HealthResponse(status="ok", service=self.SERVICE_NAME)
