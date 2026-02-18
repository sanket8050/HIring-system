# Hiring Search Service

A FastAPI-based search service that queries candidate data from MongoDB. HR users can search using natural language (e.g., *"Python developer from Pune with 2 years experience"*). Uses **Gemini 2.5 Flash** to parse queries and returns matching candidate IDs or full details.

## Features

- **Natural language search** – HR asks in plain English; the service extracts skills, location, and experience
- **MongoDB integration** – Connects to `recruitment_db/candidates` where resume sentiment/analysis is stored
- **Flexible response** – Returns full candidate info or just IDs for integration with your main app
- **REST API** – Easy to integrate from any frontend or backend

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and set your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
- `MONGO_URI` – Already set to your recruitment DB (optional to change)
- `GEMINI_API_KEY` – Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- `GEMINI_MODEL` – Model name (default: `gemini-2.5-flash`; fallback: `gemini-2.0-flash`)

### 3. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: **http://localhost:8000/docs**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates/search` | Search with natural language or filters |
| GET | `/api/candidates/search/ids` | Returns only array of IDs |
| GET | `/health` | Health check |

### Search Examples

**Natural language:**
```
GET /api/candidates/search?q=penetration%20testing%20skilled%20person%20from%20Chennai%20with%206%20years
```

**With explicit filters:**
```
GET /api/candidates/search?q=developer&skills=Python,AWS&location=Pune&min_years=2&ids_only=true
```

**IDs only:**
```
GET /api/candidates/search/ids?q=xyz%20skilled%20person%20from%20pune%20with%202%20years
```

## Integration with Your Main Application

Call the search service from your main hiring app:

```python
# Example: Python client
import httpx

response = httpx.get(
    "http://localhost:8000/api/candidates/search",
    params={"q": "Python developer from Pune with 2 years", "ids_only": True}
)
ids = response.json()["ids_only"]
```

```javascript
// Example: JavaScript/Fetch
const res = await fetch(
  'http://localhost:8000/api/candidates/search?q=Python+from+Pune&ids_only=true'
);
const { ids_only } = await res.json();
```

## Data Structure

Candidates in MongoDB follow this structure (from your resume analysis pipeline):

```json
{
  "_id": "ObjectId(...)",
  "output": {
    "candidate": { "first_name", "last_name", "email", "location", ... },
    "summary": { "years_experience", "technical_skills", "current_role", ... },
    "fit_score": { "overall", "reasoning" }
  }
}
```

## License

MIT
