from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema for the /health endpoint response."""

    status: str = "ok"
    version: str
