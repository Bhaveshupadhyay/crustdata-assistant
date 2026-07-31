# Crustdata AI Assistant MVP

An AI-powered assistant that helps users discover and use Crustdata API endpoints. Ask natural language questions like "how do I get job data?" and receive the exact API endpoint, request schema, and a ready-to-use curl command.

## Architecture

The application is structured modularly:

```text
src/
├── main.py              # FastAPI application entry point
├── agents/              # AI agents logic and orchestration
├── api/                 # API route handlers (e.g., chat endpoints)
├── core/                # Core configurations, lifecycle, and settings
├── models/              # Domain models and entities
├── repositories/        # Data access layer (knowledge base interactions)
├── schema/              # Pydantic request and response schemas
├── services/            # Business logic layer (assistant and LLM services)
└── shared/              # Shared utilities and helpers
```

## Local Development Setup

This project uses `uv` for extremely fast dependency management.

1. Install dependencies:
```bash
uv sync
```

2. Set environment variables:
```bash
cp .env.example .env
```
Ensure you set your `GEMINI_API_KEY` in the `.env` file.

3. Run the development server:
```bash
uv run uvicorn src.main:app --reload --port 8000
```

## Running with Docker

The application includes an optimized, multi-stage `Dockerfile` running as a non-root user.

1. Build the image:
```bash
docker build -t crustdata-ai-assistant .
```

2. Run the container:
```bash
docker run -p 10000:10000 --env-file .env crustdata-ai-assistant
```

## CI/CD and Deployment

This project is fully configured for automated continuous deployment to Render via Docker.

- **Infrastructure as Code**: The `render.yaml` file defines the Docker web service configuration.
- **CI/CD Pipeline**: GitHub Actions (`.github/workflows/deploy.yml`) automatically runs tests (`pytest`) and linting (`ruff`) on every push and pull request to the `main` branch. 
- **Deployments**: Upon successful tests on the `main` branch, the pipeline automatically triggers a deployment to Render via a deploy hook.

## API Usage

Example request to the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "how do I search for job data?"}'
```
