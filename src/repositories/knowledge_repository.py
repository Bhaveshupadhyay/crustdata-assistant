"""Knowledge repository — the single source of truth for Crustdata API endpoint metadata.

This is the *data access layer*. It stores all endpoint documentation in memory
and exposes query methods that the service layer uses to find relevant endpoints
for a user's question.

In a production system this would be backed by a vector database (e.g. Pinecone,
pgvector) for semantic search. For the MVP we use keyword matching over an
in-memory list, which is fast, dependency-free, and easy to extend.
"""

from __future__ import annotations

from src.models.api_docs import ApiEndpoint, EndpointParameter

# ---------------------------------------------------------------------------
# Default headers every Crustdata endpoint requires
# ---------------------------------------------------------------------------
_DEFAULT_HEADERS = {
    "Authorization": "Bearer <YOUR_API_KEY>",
    "Content-Type": "application/json",
    "x-api-version": "2025-11-01",
}


def _h(**overrides: str) -> dict[str, str]:
    """Return the standard header set, optionally overriding values."""
    return {**_DEFAULT_HEADERS, **overrides}


# ---------------------------------------------------------------------------
# Complete endpoint catalogue
# ---------------------------------------------------------------------------
_ENDPOINTS: list[ApiEndpoint] = [
    # ── Company Search ────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="company_search",
        category="company",
        name="Search Companies",
        method="POST",
        url="https://api.crustdata.com/screener/company/search",
        description=(
            "Search the Crustdata company database using structured filter conditions. "
            "Supports complex AND/OR filter logic, cursor-based pagination, sorting, and "
            "field selection. Filter by industry, headcount, funding, location, and more."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description=(
                    "Array of filter objects. Each has filter_type (e.g. INDUSTRY, HEADCOUNT, "
                    "LOCATION, FOUNDED_YEAR, FUNDING_TOTAL), type (in, equals, greater_than, "
                    "less_than), and value."
                ),
            ),
            EndpointParameter(name="page", type="integer", description="Page number (default: 1)"),
            EndpointParameter(
                name="limit",
                type="integer",
                description="Results per page (default: 20, max: 100)",
            ),
            EndpointParameter(
                name="sort_by", type="string", description="Field name to sort results by"
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/screener/company/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "HEADCOUNT", "type": "greater_than", "value": 50},
      {"filter_type": "INDUSTRY", "type": "in", "value": ["Artificial Intelligence"]}
    ],
    "limit": 10
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/search/introduction",
        tags=[
            "search", "company", "filter", "firmographic", "industry", "headcount",
            "funding", "location", "screener", "database",
        ],
    ),
    # ── Company Enrich ────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="company_enrich",
        category="company",
        name="Enrich Company",
        method="POST",
        url="https://api.crustdata.com/company/enrich",
        description=(
            "Get comprehensive company data including firmographics, headcount trends, "
            "funding rounds, tech stack, web traffic, employee reviews, key people, news, "
            "and more. Identify the company by domain, name, LinkedIn URL, or Crustdata ID."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="company_domain", type="string", description="Company website domain"
            ),
            EndpointParameter(name="company_name", type="string", description="Company name"),
            EndpointParameter(
                name="linkedin_url", type="string", description="LinkedIn company URL"
            ),
            EndpointParameter(
                name="enrich_realtime",
                type="boolean",
                description="Enable real-time fresh data retrieval (default: false)",
            ),
            EndpointParameter(
                name="fields",
                type="array of string",
                description="Specific field groups to include in the response",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/company/enrich' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "company_domain": "openai.com",
    "enrich_realtime": true
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/enrichment/introduction",
        tags=[
            "enrich", "company", "domain", "firmographic", "funding", "headcount",
            "tech stack", "enrichment", "profile", "details",
        ],
    ),
    # ── Company Identify ──────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="company_identify",
        category="company",
        name="Identify Company",
        method="POST",
        url="https://api.crustdata.com/company/identify",
        description=(
            "Match a company by name, website domain, profile URL, or Crustdata company ID. "
            "Returns one or more matches ranked by confidence score. Useful for entity "
            "resolution before enrichment."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="query",
                type="string",
                required=True,
                description="Partial company name, domain, or URL to resolve",
            ),
            EndpointParameter(
                name="country",
                type="string",
                description="Country code for disambiguation (e.g. 'US')",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/company/identify' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "query": "Crustdata"
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/identify/introduction",
        tags=[
            "identify", "company", "resolve", "match", "entity resolution",
            "lookup", "find", "name", "domain",
        ],
    ),
    # ── Company Autocomplete ──────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="company_autocomplete",
        category="company",
        name="Company Autocomplete",
        method="POST",
        url="https://api.crustdata.com/company/search/autocomplete",
        description=(
            "Returns field value suggestions with document counts for company search fields. "
            "Useful for discovering valid filter values before building search queries."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="field",
                type="string",
                required=True,
                description="Field path, e.g. 'company.basic_info.name' or 'industry'",
            ),
            EndpointParameter(
                name="query",
                type="string",
                required=True,
                description="Partial prefix text to get suggestions for",
            ),
            EndpointParameter(
                name="limit", type="integer", description="Number of suggestions (default: 10)"
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/company/search/autocomplete' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "field": "company.basic_info.name",
    "query": "Crust",
    "limit": 5
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/autocomplete/introduction",
        tags=[
            "autocomplete", "company", "suggest", "typeahead", "field values",
            "filter values", "search helper",
        ],
    ),
    # ── Person Search ─────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="person_search",
        category="person",
        name="Search People",
        method="POST",
        url="https://api.crustdata.com/screener/person/search",
        description=(
            "Search the Crustdata person database using flexible filter conditions, sorting, "
            "and cursor-based pagination. Filter by job title, company, location, seniority, "
            "industry, education, skills, experience years, and more."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description=(
                    "Array of filter objects. Each has filter_type (e.g. TITLE, CURRENT_COMPANY, "
                    "LOCATION, SKILLS, EXPERIENCE_YEARS), type (in, equals, contains), and value."
                ),
            ),
            EndpointParameter(name="page", type="integer", description="Page number (default: 1)"),
            EndpointParameter(
                name="limit",
                type="integer",
                description="Results per page (default: 20, max: 100)",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/screener/person/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "TITLE", "type": "in", "value": ["CTO", "VP Engineering"]},
      {"filter_type": "LOCATION", "type": "in", "value": ["San Francisco, CA"]}
    ],
    "limit": 5
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/search/introduction",
        tags=[
            "search", "person", "people", "filter", "title", "company",
            "location", "skills", "seniority", "screener", "professional",
        ],
    ),
    # ── Person Enrich ─────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="person_enrich",
        category="person",
        name="Enrich Person",
        method="POST",
        url="https://api.crustdata.com/person/enrich",
        description=(
            "Enrich person records using the Crustdata dataset. Provide LinkedIn profile URLs "
            "to retrieve detailed person data including employment history, education, skills, "
            "and developer platform data. Supports batch enrichment of up to 25 profiles."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="linkedin_profile_url",
                type="string",
                description="LinkedIn profile URL of the person to enrich",
            ),
            EndpointParameter(
                name="person_id", type="string", description="Crustdata person ID"
            ),
            EndpointParameter(
                name="enrich_realtime",
                type="boolean",
                description="Enable real-time fresh data retrieval (default: false)",
            ),
            EndpointParameter(
                name="include_developer_profiles",
                type="boolean",
                description="Include GitHub/StackOverflow handles",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/person/enrich' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "linkedin_profile_url": "https://www.linkedin.com/in/satyanadella/"
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/enrichment/introduction",
        tags=[
            "enrich", "person", "people", "profile", "linkedin", "experience",
            "education", "skills", "developer", "enrichment",
        ],
    ),
    # ── Person Contact Enrich ─────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="person_contact_enrich",
        category="person",
        name="Person Contact Enrich",
        method="POST",
        url="https://api.crustdata.com/person/enrich/contact",
        description=(
            "Enrich only the contact data for a person — business emails, personal emails, "
            "and phone numbers. Provide either a LinkedIn profile URL or a business email. "
            "Supports batch enrichment of up to 25 identifiers at once."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="linkedin_profile_url",
                type="string",
                description="LinkedIn profile URL",
            ),
            EndpointParameter(
                name="work_email",
                type="string",
                description="Work email for reverse lookup",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/person/enrich/contact' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "linkedin_profile_url": "https://www.linkedin.com/in/example-profile/"
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/contact/enrich",
        tags=[
            "contact", "email", "phone", "person", "enrich", "business email",
            "personal email", "phone number", "reverse lookup",
        ],
    ),
    # ── Person Autocomplete ───────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="person_autocomplete",
        category="person",
        name="Person Autocomplete",
        method="POST",
        url="https://api.crustdata.com/person/search/autocomplete",
        description=(
            "Return ranked field-value suggestions for person search fields. Useful for "
            "discovering valid filter values for job titles, skills, companies, etc."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="field",
                type="string",
                required=True,
                description="Target field (e.g. 'job_title', 'skill', 'company.basic_info.name')",
            ),
            EndpointParameter(
                name="query",
                type="string",
                required=True,
                description="Partial prefix string",
            ),
            EndpointParameter(
                name="limit", type="integer", description="Suggestion count (default: 10)"
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/person/search/autocomplete' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "field": "job_title",
    "query": "Data Sci",
    "limit": 5
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/autocomplete/introduction",
        tags=[
            "autocomplete", "person", "suggest", "typeahead", "field values",
            "title", "skills",
        ],
    ),
    # ── Job Search ────────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="job_search",
        category="job",
        name="Search Jobs",
        method="POST",
        url="https://api.crustdata.com/job/search",
        description=(
            "Search the Crustdata job dataset using filter conditions. Each result includes "
            "the job's details (title, category, URL, openings), the hiring company's core "
            "firmographics, the job location, full job description text, and metadata. "
            "Filter by job title, company domain, location, and date posted."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description=(
                    "Array of filter objects. Each has filter_type (e.g. JOB_TITLE, "
                    "COMPANY_DOMAIN, LOCATION, DATE_POSTED), type (in, equals, greater_than), "
                    "and value."
                ),
            ),
            EndpointParameter(name="page", type="integer", description="Page number (default: 1)"),
            EndpointParameter(
                name="limit",
                type="integer",
                description="Results per page (default: 20, max: 100)",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/job/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "COMPANY_DOMAIN", "type": "in", "value": ["stripe.com"]},
      {"filter_type": "LOCATION", "type": "in", "value": ["Remote"]}
    ],
    "limit": 20
  }'""",
        doc_url="https://docs.crustdata.com/job-docs/search/introduction",
        tags=[
            "search", "job", "jobs", "listing", "hiring", "title",
            "company", "location", "remote", "openings", "career",
        ],
    ),
    # ── Job Autocomplete ──────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="job_autocomplete",
        category="job",
        name="Job Autocomplete",
        method="POST",
        url="https://api.crustdata.com/job/search/autocomplete",
        description=(
            "Return type-ahead suggestions for job search field values. Useful for "
            "discovering valid filter values for job titles, categories, locations, etc."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="field",
                type="string",
                required=True,
                description="Field path (e.g. 'title', 'location', 'category')",
            ),
            EndpointParameter(
                name="query",
                type="string",
                required=True,
                description="Partial prefix input",
            ),
            EndpointParameter(
                name="limit", type="integer", description="Suggestion count (default: 10)"
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/job/search/autocomplete' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "field": "title",
    "query": "Product Man",
    "limit": 5
  }'""",
        doc_url="https://docs.crustdata.com/job-docs/autocomplete/introduction",
        tags=[
            "autocomplete", "job", "suggest", "typeahead", "title",
            "category", "location",
        ],
    ),
    # ── Web Search ────────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="web_search",
        category="web",
        name="Web Search",
        method="POST",
        url="https://api.crustdata.com/web/search/live",
        description=(
            "Perform a real-time web search query and return results from multiple sources "
            "including web, news, academic articles, deep research, and social media. "
            "Use for competitive intelligence, market research, and content discovery."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="query",
                type="string",
                required=True,
                description="Web search query string",
            ),
            EndpointParameter(
                name="num_results",
                type="integer",
                description="Number of results to return (default: 10)",
            ),
            EndpointParameter(
                name="domain_filter",
                type="array of string",
                description="Include/exclude specific web domains",
            ),
            EndpointParameter(
                name="freshness",
                type="string",
                description="Recency filter: 'day', 'week', 'month', or 'year'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/web/search/live' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "query": "AI Agents market size 2026",
    "num_results": 10,
    "freshness": "month"
  }'""",
        doc_url="https://docs.crustdata.com/web-docs/search/introduction",
        tags=[
            "web", "search", "live", "news", "academic", "social media",
            "research", "real-time", "internet",
        ],
    ),
    # ── Web Fetch ─────────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="web_fetch",
        category="web",
        name="Web Fetch",
        method="POST",
        url="https://api.crustdata.com/web/enrich/live",
        description=(
            "Fetch the HTML content of webpages given their URLs. Retrieves the page title "
            "and full HTML/markdown/text content for up to 10 URLs in a single request. "
            "Use for content extraction, data collection, and monitoring."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="url",
                type="string",
                required=True,
                description="Target URL to fetch",
            ),
            EndpointParameter(
                name="output_format",
                type="string",
                description="Output format: 'markdown', 'html', or 'text'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/web/enrich/live' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "url": "https://crustdata.com",
    "output_format": "markdown"
  }'""",
        doc_url="https://docs.crustdata.com/web-docs/fetch/introduction",
        tags=[
            "web", "fetch", "scrape", "html", "content", "url",
            "page", "extract", "crawl",
        ],
    ),
    # ── Company Discovery Watcher ─────────────────────────────────────
    ApiEndpoint(
        endpoint_id="watcher_company_discovery",
        category="watcher",
        name="Company Discovery Watcher",
        method="POST",
        url="https://api.crustdata.com/watch/company/discovery",
        description=(
            "Turn a company search into a recurring feed. Re-runs your filters on a schedule "
            "and pushes new matching companies to a webhook or Slack."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description="Company search filter criteria",
            ),
            EndpointParameter(
                name="frequency",
                type="string",
                required=True,
                description="Schedule: 'daily' or 'weekly'",
            ),
            EndpointParameter(
                name="webhook_url",
                type="string",
                required=True,
                description="Webhook URL for notifications",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/watch/company/discovery' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "HEADCOUNT", "type": "greater_than", "value": 100}
    ],
    "frequency": "weekly",
    "webhook_url": "https://example.com/webhook"
  }'""",
        doc_url="https://docs.crustdata.com/watcher-docs/company/discovery",
        tags=[
            "watcher", "company", "discovery", "monitor", "recurring",
            "webhook", "notification", "alert", "schedule",
        ],
    ),
    # ── Company Entity Watcher ────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="watcher_company_entity",
        category="watcher",
        name="Company Entity Watcher",
        method="POST",
        url="https://api.crustdata.com/watch/company/entity",
        description=(
            "Watch a list of companies and get notified when a profile changes — headcount "
            "move, funding round, news mention, or rebrand. You supply the list; the watcher "
            "delivers the diff."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="company_domains",
                type="array of string",
                required=True,
                description="Company domains to watch",
            ),
            EndpointParameter(
                name="webhook_url",
                type="string",
                required=True,
                description="Webhook URL for change alerts",
            ),
            EndpointParameter(
                name="frequency",
                type="string",
                required=True,
                description="Schedule: 'daily' or 'weekly'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/watch/company/entity' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "company_domains": ["stripe.com", "openai.com"],
    "webhook_url": "https://example.com/webhook",
    "frequency": "daily"
  }'""",
        doc_url="https://docs.crustdata.com/watcher-docs/company/entity",
        tags=[
            "watcher", "company", "entity", "monitor", "track",
            "changes", "diff", "webhook", "funding", "headcount",
        ],
    ),
    # ── Person Discovery Watcher ──────────────────────────────────────
    ApiEndpoint(
        endpoint_id="watcher_person_discovery",
        category="watcher",
        name="Person Discovery Watcher",
        method="POST",
        url="https://api.crustdata.com/watch/person/discovery",
        description=(
            "Turn a person search filter into a recurring feed. Re-runs your filters on a "
            "schedule and pushes new matching people to a webhook or Slack."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description="Person search filter criteria",
            ),
            EndpointParameter(
                name="webhook_url",
                type="string",
                required=True,
                description="Target webhook URL",
            ),
            EndpointParameter(
                name="frequency",
                type="string",
                required=True,
                description="Schedule: 'daily' or 'weekly'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/watch/person/discovery' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "TITLE", "type": "in", "value": ["Head of AI"]}
    ],
    "webhook_url": "https://example.com/webhook",
    "frequency": "weekly"
  }'""",
        doc_url="https://docs.crustdata.com/watcher-docs/person/discovery",
        tags=[
            "watcher", "person", "discovery", "monitor", "recurring",
            "webhook", "hiring", "alert",
        ],
    ),
    # ── Person Entity Watcher ─────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="watcher_person_entity",
        category="watcher",
        name="Person Entity Watcher",
        method="POST",
        url="https://api.crustdata.com/watch/person/entity",
        description=(
            "Watch a list of people and get notified when their profile changes — "
            "a new job, title promotion, or new company affiliation."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="person_urls",
                type="array of string",
                required=True,
                description="LinkedIn profile URLs to watch",
            ),
            EndpointParameter(
                name="webhook_url",
                type="string",
                required=True,
                description="Webhook URL for change alerts",
            ),
            EndpointParameter(
                name="frequency",
                type="string",
                required=True,
                description="Schedule: 'daily' or 'weekly'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/watch/person/entity' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "person_urls": ["https://www.linkedin.com/in/example-profile/"],
    "webhook_url": "https://example.com/webhook",
    "frequency": "daily"
  }'""",
        doc_url="https://docs.crustdata.com/watcher-docs/person/entity",
        tags=[
            "watcher", "person", "entity", "monitor", "track",
            "job change", "promotion", "webhook",
        ],
    ),
    # ── Batch Company Search ──────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_company_search",
        category="batch",
        name="Batch Search Companies",
        method="POST",
        url="https://api.crustdata.com/batch/company/search",
        description=(
            "Run one company database search query asynchronously and receive up to "
            "10,000 matching companies as a single results file."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description="Same filter format as /screener/company/search",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/company/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "INDUSTRY", "type": "in", "value": ["FinTech"]}
    ]
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/search/batch-search",
        tags=["batch", "company", "search", "async", "bulk", "large", "10000"],
    ),
    # ── Batch Company Enrich ──────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_company_enrich",
        category="batch",
        name="Batch Enrich Companies",
        method="POST",
        url="https://api.crustdata.com/batch/company/enrich",
        description=(
            "Enrich up to 10,000 companies in a single asynchronous job. Provide exactly "
            "one identifier type: names, domains, profile URLs, or Crustdata company IDs."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="domains",
                type="array of string",
                description="Company domains to enrich",
            ),
            EndpointParameter(
                name="names",
                type="array of string",
                description="Company names to enrich",
            ),
            EndpointParameter(
                name="fields",
                type="array of string",
                description="Specific field groups to include",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/company/enrich' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "domains": ["stripe.com", "openai.com", "crustdata.com"]
  }'""",
        doc_url="https://docs.crustdata.com/company-docs/enrichment/batch",
        tags=["batch", "company", "enrich", "bulk", "async", "mass enrichment"],
    ),
    # ── Batch Person Search ───────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_person_search",
        category="batch",
        name="Batch Search People",
        method="POST",
        url="https://api.crustdata.com/batch/person/search",
        description=(
            "Run one person database search query asynchronously and receive up to "
            "10,000 matching people as a single results file."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description="Same filter format as /screener/person/search",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/person/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "TITLE", "type": "in", "value": ["Machine Learning Engineer"]}
    ]
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/search/batch-search",
        tags=["batch", "person", "search", "async", "bulk", "large"],
    ),
    # ── Batch Person Enrich ───────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_person_enrich",
        category="batch",
        name="Batch Enrich People",
        method="POST",
        url="https://api.crustdata.com/batch/person/enrich",
        description=(
            "Enrich up to 10,000 people in a single asynchronous job. Provide LinkedIn "
            "profile URLs or business emails."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="professional_network_profile_urls",
                type="array of string",
                description="LinkedIn profile URLs to enrich",
            ),
            EndpointParameter(
                name="business_emails",
                type="array of string",
                description="Business emails to enrich",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/person/enrich' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "professional_network_profile_urls": [
      "https://www.linkedin.com/in/satyanadella/",
      "https://www.linkedin.com/in/example/"
    ]
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/enrichment/batch-enrich",
        tags=["batch", "person", "enrich", "bulk", "async", "mass enrichment"],
    ),
    # ── Batch Job Search ──────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_job_search",
        category="batch",
        name="Batch Search Jobs",
        method="POST",
        url="https://api.crustdata.com/batch/job/search",
        description=(
            "Retrieve every job listing for up to 10 companies in a single asynchronous job."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="filters",
                type="array of objects",
                required=True,
                description="Same filter format as /job/search",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/job/search' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "filters": [
      {"filter_type": "COMPANY_DOMAIN", "type": "in", "value": ["google.com"]}
    ]
  }'""",
        doc_url="https://docs.crustdata.com/job-docs/search/introduction",
        tags=["batch", "job", "search", "async", "bulk"],
    ),
    # ── Batch Contact Enrich ──────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_contact_enrich",
        category="batch",
        name="Batch Contact Enrich",
        method="POST",
        url="https://api.crustdata.com/batch/person/contact/enrich",
        description=(
            "Enrich contact information (business email, personal emails, phone numbers) "
            "for up to 300 people in a single asynchronous job."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="professional_network_profile_urls",
                type="array of string",
                required=True,
                description="LinkedIn profile URLs",
            ),
            EndpointParameter(
                name="fields",
                type="array of string",
                required=True,
                description="Contact types: 'business_email', 'personal_emails', 'phone_numbers'",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/person/contact/enrich' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "professional_network_profile_urls": [
      "https://www.linkedin.com/in/example-profile/"
    ],
    "fields": ["business_email", "personal_emails", "phone_numbers"]
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/contact/batch",
        tags=["batch", "contact", "enrich", "email", "phone", "bulk"],
    ),
    # ── Batch Identify Person ─────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_identify_person",
        category="batch",
        name="Batch Identify Person (Reverse Email Lookup)",
        method="POST",
        url="https://api.crustdata.com/batch/person/identify",
        description=(
            "Resolve a bulk list of emails (business or personal, including Gmail) to the "
            "people behind them — reverse email lookup. The only endpoint that matches "
            "personal email addresses."
        ),
        headers=_h(),
        body_parameters=[
            EndpointParameter(
                name="emails",
                type="array of string",
                description="Email addresses to resolve",
            ),
            EndpointParameter(
                name="professional_network_profile_urls",
                type="array of string",
                description="LinkedIn URLs to resolve",
            ),
        ],
        curl_example="""\
curl -X POST 'https://api.crustdata.com/batch/person/identify' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "emails": ["user@example.com", "user@gmail.com"]
  }'""",
        doc_url="https://docs.crustdata.com/person-docs/contact/identify",
        tags=[
            "batch", "identify", "reverse lookup", "email", "personal email",
            "gmail", "resolve", "person",
        ],
    ),
    # ── Get Batch Job Status ──────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_status",
        category="batch",
        name="Get Batch Job Status",
        method="GET",
        url="https://api.crustdata.com/batch/{batch_id}",
        description=(
            "Poll the current state of a batch job. Status moves pending → processing → "
            "completed or failed. When completed, includes download_url for results."
        ),
        headers=_h(),
        body_parameters=[],
        curl_example="""\
curl -X GET 'https://api.crustdata.com/batch/YOUR_BATCH_ID' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01'""",
        doc_url="https://docs.crustdata.com/api-reference/batch-apis/get-the-status-and-download-urls-for-a-batch-job",
        tags=["batch", "status", "poll", "download", "results"],
    ),
    # ── List Batch Jobs ───────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="batch_list",
        category="batch",
        name="List Batch Jobs",
        method="GET",
        url="https://api.crustdata.com/batch",
        description=(
            "List your batch jobs, most recent first, with cursor-based pagination "
            "and optional status filtering."
        ),
        headers=_h(),
        body_parameters=[],
        curl_example="""\
curl -X GET 'https://api.crustdata.com/batch' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01'""",
        doc_url="https://docs.crustdata.com/api-reference/batch-apis/list-batch-jobs-for-the-authenticated-account",
        tags=["batch", "list", "jobs", "history"],
    ),
    # ── Credits ───────────────────────────────────────────────────────
    ApiEndpoint(
        endpoint_id="account_credits",
        category="general",
        name="Check Credits",
        method="GET",
        url="https://api.crustdata.com/account/credits",
        description=(
            "Check your remaining Crustdata API credit balance and recurring credit "
            "grant with a single free GET request."
        ),
        headers={"Authorization": "Bearer <YOUR_API_KEY>", "x-api-version": "2025-11-01"},
        body_parameters=[],
        curl_example="""\
curl -X GET 'https://api.crustdata.com/account/credits' \\
  -H 'Authorization: Bearer <YOUR_API_KEY>' \\
  -H 'x-api-version: 2025-11-01'""",
        doc_url="https://docs.crustdata.com/general/credits",
        tags=["credits", "balance", "account", "billing", "usage", "quota"],
    ),
]


class KnowledgeRepository:
    """In-memory repository of Crustdata API endpoint documentation.

    Provides fast keyword-based search across the endpoint catalogue.
    Designed to be swapped for a vector-DB implementation later.
    """

    def __init__(self, db: list[ApiEndpoint]) -> None:
        self._endpoints: list[ApiEndpoint] = db

    # ------------------------------------------------------------------
    # Public query interface
    # ------------------------------------------------------------------

    def get_all_endpoints(self) -> list[ApiEndpoint]:
        """Return every registered endpoint."""
        return list(self._endpoints)

    def get_by_id(self, endpoint_id: str) -> ApiEndpoint | None:
        """Exact lookup by endpoint slug."""
        for ep in self._endpoints:
            if ep.endpoint_id == endpoint_id:
                return ep
        return None

    def get_by_category(self, category: str) -> list[ApiEndpoint]:
        """Return all endpoints in a category (company, person, job, web, watcher, batch)."""
        category_lower = category.lower()
        return [ep for ep in self._endpoints if ep.category == category_lower]

    def search(self, query: str, limit: int = 5) -> list[ApiEndpoint]:
        """Keyword-based search across endpoint names, descriptions, and tags.

        Scores are computed by counting how many query tokens appear in the
        searchable text of each endpoint. Higher score = better match.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scored: list[tuple[float, ApiEndpoint]] = []
        for ep in self._endpoints:
            score = self._score(ep, tokens)
            if score > 0:
                scored.append((score, ep))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [ep for _, ep in scored[:limit]]

    def build_context_block(self, endpoints: list[ApiEndpoint]) -> str:
        """Serialize a list of endpoints into a markdown context block that
        can be injected directly into an LLM prompt."""
        parts: list[str] = []
        for ep in endpoints:
            params_text = ""
            if ep.body_parameters:
                lines = []
                for p in ep.body_parameters:
                    req = " (required)" if p.required else ""
                    lines.append(f"  - `{p.name}` ({p.type}{req}): {p.description}")
                params_text = "\n".join(lines)

            part = (
                f"### {ep.name}\n"
                f"- **Endpoint:** `{ep.method} {ep.url}`\n"
                f"- **Description:** {ep.description}\n"
                f"- **Docs:** {ep.doc_url}\n"
            )
            if params_text:
                part += f"- **Body Parameters:**\n{params_text}\n"
            if ep.curl_example:
                part += f"- **Curl Example:**\n```bash\n{ep.curl_example}\n```\n"
            parts.append(part)

        return "\n---\n".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase and split into word tokens."""
        return [t for t in text.lower().split() if len(t) >= 2]

    @staticmethod
    def _score(endpoint: ApiEndpoint, tokens: list[str]) -> float:
        """Score an endpoint against the given search tokens."""
        # Build a single searchable string from all endpoint fields.
        searchable = " ".join(
            [
                endpoint.name.lower(),
                endpoint.description.lower(),
                endpoint.category.lower(),
                " ".join(t.lower() for t in endpoint.tags),
                endpoint.endpoint_id.replace("_", " "),
            ]
        )
        score = 0.0
        for token in tokens:
            if token in searchable:
                score += 1.0
                # Bonus for exact tag match
                if token in [t.lower() for t in endpoint.tags]:
                    score += 0.5
                # Bonus for category match
                if token == endpoint.category.lower():
                    score += 0.5
        return score
