"""Domain model for a Crustdata API endpoint stored in the knowledge base."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EndpointParameter(BaseModel):
    """A single request parameter or body field."""

    name: str
    type: str = "string"
    required: bool = False
    description: str = ""


class ApiEndpoint(BaseModel):
    """Represents one Crustdata API endpoint with all the metadata an LLM needs
    to answer user questions and generate curl examples."""

    endpoint_id: str = Field(..., description="Unique slug, e.g. 'company_search'")
    category: str = Field(..., description="API group: company, person, job, web, watcher, batch")
    name: str = Field(..., description="Human-readable name")
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Full URL path")
    description: str = Field(..., description="Detailed description of what the endpoint does")
    headers: dict[str, str] = Field(default_factory=dict)
    body_parameters: list[EndpointParameter] = Field(default_factory=list)
    curl_example: str = Field(default="", description="A working curl example")
    doc_url: str = Field(default="", description="Link to the official docs page")
    tags: list[str] = Field(
        default_factory=list,
        description="Search keywords — e.g. ['search', 'filter', 'company', 'firmographic']",
    )
