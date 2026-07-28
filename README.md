# Crustdata AI Assistant MVP

An AI-powered assistant that helps users discover and use Crustdata API endpoints. 
Ask natural language questions like "how do I get job data?" and receive the exact 
API endpoint, request schema, and a ready-to-use curl command.

## Architecture

```
src/
├── main.py                  # FastAPI application entry point
├── config.py                # Application settings (env vars)
├── models/                  # Pydantic request/response schemas
│   ├── chat.py
│   └── api_docs.py
├── repositories/            # Data access layer (knowledge base)
│   └── knowledge_repository.py
├── services/                # Business logic layer
│   ├── assistant_service.py
│   └── llm_service.py
└── api/                 # API route handlers
    └── chat_router.py
```

## Setup

```bash
# Install dependencies
pip install -e .

# Set environment variable
export GEMINI_API_KEY="your-gemini-api-key"

# Run the server
uvicorn src.main:app --reload --port 8000
```

## API Usage

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "how do I search for job data?"}'
```
