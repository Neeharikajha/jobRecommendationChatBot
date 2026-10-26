# Hidani Job Assistant

A conversational AI driven job matching and application tracking system. Parses resumes, recommends relevant positions, records applications, and supports natural language interactions.

---

## Overview

Hidani Job Assistant is an end-to-end job recommendation platform leveraging large language models to match candidates with relevant job opportunities. It uses Google Gemini for natural language understanding, resume parsing, and intelligent job matching.

### Key Capabilities

- Resume parsing from PDF and DOCX files with structured data extraction
- Intelligent job matching based on skills, experience level, and role preferences
- Natural language conversation interface for job search, filtering, and application tracking
- Session-based application management with persistent history
- Support for role filtering, remote job search, and compound queries

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Frontend Layer                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  TypeScript UI - Chat interface with resume upload, job cards, application list │  │
│  │  - Chat bubble rendering                                                         │  │
│  │  - Job detail expandable cards with apply actions                                │  │
│  │  - Application history table                                                     │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓ HTTP API
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              Django REST Backend                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Views: UploadView, ChatView                                                    │  │
│  │  - Resume upload with parsing                                                   │  │
│  │  - Message routing to orchestrator                                              │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              Agent Orchestrator                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Intent Classification Engine                                                   │  │
│  │  - Routes user queries to appropriate handlers                                  │  │
│  │  - Handles: search_jobs, apply_jobs, view_applications, remove_application     │  │
│  │  - Profile roles query, natural language Q&A                                    │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
│                                      ↓                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Gemini Auto Functions                                                          │  │
│  │  - search_jobs Tool                                                             │  │
│  │  - get_job_details Tool                                                         │  │
│  │  - apply_to_job Tool                                                            │  │
│  │  - get_applications Tool                                                        │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             Matching & Parsing Layers                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Matcher Engine                                                                 │  │
│  │  - Skill-based scoring                                                          │  │
│  │  - Experience level filtering                                                   │  │
│  │  - Role type classification (frontend, backend, fullstack, devops, data)        │  │
│  │  - Remote location filtering                                                    │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Resume Parser                                                                  │  │
│  │  - PDF text extraction (pdfplumber)                                             │  │
│  │  - DOCX parsing (python-docx)                                                   │  │
│  │  - LLM structured data extraction                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  Data Layer                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Database Models (Django ORM)                                                   │  │
│  │  - Resume (session_key, data JSON)                                              │  │
│  │  - Application (session_key, job_id, status)                                    │  │
│  │  - Message (session_key, role, content)                                         │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Job Dataset (JSON)                                                             │  │
│  │  - 1500+ jobs cached in LRU cache                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

1. **Resume Upload Flow**
   - User uploads PDF or DOCX via file input
   - File type detected via magic bytes
   - Text extracted with pdfplumber or python-docx
   - LLM extracts structured data (skills, experience, education, projects)
   - Resume stored in database with session key

2. **Chat Interaction Flow**
   - User sends natural language message
   - Intent classifier determines action type
   - Orchestrator executes appropriate handler
   - Tool calls executed via Gemini Auto Functions
   - Response formatted and returned to frontend
   - Conversation persisted to database

3. **Job Matching Flow**
   - User requests job search with optional filters
   - Matcher applies skill matching, experience filtering, role type classification
   - Jobs scored and sorted by relevance
   - Results returned with match reasons

---

## APIs Used

### External APIs

| API               | Purpose                                                 | Provider |
| ----------------- | ------------------------------------------------------- | -------- |
| Google Gemini API | LLM for resume parsing, chat agent, job recommendations | Google   |
| Indeed API        | Job listing data (via jobspy library)                   | Indeed   |
| LinkedIn API      | Job listing data (via jobspy library)                   | LinkedIn |

### Internal APIs

| Endpoint       | Method | Description                                   |
| -------------- | ------ | --------------------------------------------- |
| `/api/upload/` | POST   | Upload and parse resume (multipart/form-data) |
| `/api/chat/`   | POST   | Send message to agent (JSON body)             |

### Agent Tools

| Tool Name          | Purpose                                |
| ------------------ | -------------------------------------- |
| `search_jobs`      | Find jobs matching resume with filters |
| `get_job_details`  | Get full details of a single job       |
| `apply_to_job`     | Record application for a job           |
| `get_applications` | List all user applications             |

---

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- Google Gemini API key from Google AI Studio

### Installation

```bash
# Clone repository
git clone <repository_url>
cd hidani-job-assistant

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your Gemini API key and Django settings

# Run database migrations
python manage.py migrate

# Build frontend assets
npm run build

# Start development server
python manage.py runserver
```

---

## Configuration

### Environment Variables

| Variable       | Description                                 | Required               |
| -------------- | ------------------------------------------- | ---------------------- |
| GEMINI_API_KEY | Google Gemini API key for LLM operations    | Yes                    |
| SECRET_KEY     | Django secret key for session security      | Yes                    |
| DEBUG          | Enable development mode                     | No (default: True)     |
| ALLOWED_HOSTS  | Comma-separated list of allowed hosts       | No (default: \*)       |
| DATABASE_URL   | PostgreSQL connection string for production | No (SQLite by default) |

---

## API Endpoints

### Upload Resume

```
POST /api/upload/
Content-Type: multipart/form-data

Body:
- file: PDF or DOCX resume file
```

**Response:**

```json
{
  "resume": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "designation": "Software Engineer",
    "skills": ["python", "django", "react"],
    "experience_years": 3,
    "experience": ["Role at Company (2022-2024)"],
    "education": ["B.Tech in Computer Science"],
    "projects": ["Project Name: Description"]
  }
}
```

### Chat with Agent

```
POST /api/chat/
Content-Type: application/json

Body:
{
  "message": "find frontend jobs"
}
```

**Response:**

```json
{
  "reply": "Found 10 job(s) matching your profile",
  "type": "jobs",
  "jobs": [
    {
      "display_id": 1,
      "job_id": 123,
      "title": "Frontend Developer",
      "company": "Tech Corp",
      "location": "Remote",
      "experience_required": "2-4 years",
      "remote": true,
      "skills": ["react", "javascript"],
      "description_snippet": "We are looking for...",
      "match_reason": "3 skills match + experience fits",
      "source_link": "https://..."
    }
  ],
  "applications": null
}
```

---

## Agent Capabilities

The orchestrator agent handles the following intents:

| Intent             | Description                             | Example                                |
| ------------------ | --------------------------------------- | -------------------------------------- |
| search_jobs        | Find jobs matching resume               | "show me frontend jobs"                |
| apply_jobs         | Record application to specific jobs     | "apply to 1, 2, 3"                     |
| view_applications  | Show application history                | "show my applied jobs"                 |
| remove_application | Remove applied jobs                     | "remove 1, 2" or "remove all"          |
| profile_roles      | Suggest suitable roles based on profile | "what roles fit this job profile?"     |
| other              | General questions about resume data     | "how many years experience do I have?" |

---

## Matching Algorithm

### Scoring Components

1. **Skill Match** (20 points per skill)
   - Compares resume skills against job requirements
   - Weighted by skill relevance

2. **Experience Match** (up to 30 points)
   - 30 points if experience meets or exceeds requirement
   - 15 points if slightly junior but capable

3. **Role Title Similarity** (up to 10 points)
   - Fuzzy matching using RapidFuzz
   - Threshold of 65 similarity score

### Filtering Rules

- **Experience Level Gate**: Excludes senior roles for freshers/juniors
- **Internship Gate**: Excludes intern roles for experienced candidates
- **Role Type Filter**: Strict matching for frontend, backend, fullstack, devops, data
- **Remote Filter**: Optional remote-only filtering
- **Skill Filter**: User-specified skills via query

### Experience Level Classification

| Experience | Classification | Role Filtering                               |
| ---------- | -------------- | -------------------------------------------- |
| 0-1 years  | Fresher        | No senior roles, no roles requiring >2 years |
| 2-3 years  | Junior         | No senior roles                              |
| 4-6 years  | Mid level      | No intern roles                              |
| 7+ years   | Senior         | No intern roles                              |

---

## Scalability Considerations

### Current Architecture Limitations

- Single session-based user identification (no persistent accounts)
- In-memory job dataset (caching with LRU)
- Sequential LLM API calls (no batch processing)
- Session cookie expiration after 7 days

### Scaling Strategies

#### Horizontal Scaling

1. **Stateless Backend**
   - Move session management to Redis or database
   - Enable multiple Django instances behind load balancer
   - Use signed cookies or JWT for session tracking

2. **Database**
   - Migrate from SQLite to PostgreSQL for production
   - Add connection pooling (pgbouncer)
   - Implement database read replicas for reporting

3. **Job Dataset**
   - Move to PostgreSQL with full-text search
   - Add job indexing for faster filtering
   - Consider PostgreSQL JSONB queries for skill matching

#### Vertical Scaling

1. **Caching**
   - Redis cache for job search results
   - Cache LLM responses for common queries
   - Redis session store for faster session access

2. **LLM Optimization**
   - Implement request queuing for LLM calls
   - Use Gemini Flash for common queries, Pro for complex analysis
   - Batch processing for resume parsing

3. **Static Assets**
   - CDN for static files (JavaScript, CSS)
   - Asset optimization and compression

#### Async Processing

1. **Celery Tasks**
   - Move LLM calls to background workers
   - Process resume parsing asynchronously
   - Email notifications for job alerts

2. **WebSockets**
   - Real-time updates with Django Channels
   - Live application status updates

---

## Edge Cases and Error Handling

### Resume Parsing

| Edge Case                | Handling                                 |
| ------------------------ | ---------------------------------------- |
| Scanned PDF (image only) | Error: "No readable text found"          |
| File size > 5MB          | Error: "File too large"                  |
| Empty or corrupted file  | Error: "Could not read file"             |
| No skills detected       | Error: "This doesn't look like a resume" |

### Job Matching

| Edge Case                        | Handling                              |
| -------------------------------- | ------------------------------------- |
| No jobs match filters            | Reply: "No matching jobs found"       |
| User applies to non-existent job | Reply: "Could not find job(s)"        |
| Application already exists       | Reply: "Already applied to: X"        |
| Invalid job numbers in apply     | Reply: "Specify job numbers to apply" |

### LLM / API Errors

| Edge Case                  | Handling                                |
| -------------------------- | --------------------------------------- |
| Gemini API key missing     | Log error, return user friendly message |
| Gemini API rate limit      | Retry with exponential backoff          |
| LLM returns malformed JSON | Log error, return fallback message      |
| Network timeout            | Retry up to 3 times with delay          |

### User Session

| Edge Case                | Handling                        |
| ------------------------ | ------------------------------- |
| Session expired          | User must re-upload resume      |
| Multiple tabs            | Shared session state (expected) |
| Browser cookies disabled | Session creation may fail       |

---

## Security Considerations

### Current Security Measures

- CSRF protection enabled
- HTTPS recommended in production (SECURE_COOKIES)
- Session cookie expiration after 7 days
- Message length limit (2000 characters)
- File size limit (5MB)

### Recommended Production Enhancements

| Area              | Recommendation                         |
| ----------------- | -------------------------------------- |
| Authentication    | Add Django auth with JWT or OAuth2     |
| API Rate Limiting | Implement DRF throttling               |
| Input Validation  | Add schema validation for all inputs   |
| Sensitive Data    | Mask emails and phone numbers in logs  |
| CORS              | Configure allowed origins explicitly   |
| SQL Injection     | Already protected by Django ORM        |
| XSS               | Already protected by template escaping |

---

## Deployment Options

### Render.com (Recommended for Free Tier)

```bash
# Build command
pip install -r requirements.txt && npm install && npm run build && python manage.py migrate

# Start command
gunicorn config.wsgi:application
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY package.json package-lock.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Self-Hosted

```bash
# Install supervisor or systemd service
# Configure Gunicorn with multiple workers
# Setup Nginx as reverse proxy
# Enable HTTPS with Let's Encrypt
```

---

## Development

### Project Structure

```
hidani-job-assistant/
├── agents/               # Multi-agent system
│   ├── orchestrator.py  # Main conversation flow
│   ├── llm.py           # Gemini client
│   ├── resume_parser.py # PDF/DOCX parsing
│   ├── matcher.py       # Job matching algorithm
│   ├── tools.py         # Tool implementations
│   ├── prompts.py       # System prompts
│   └── __init__.py
├── chat/                # Django app
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   └── urls.py          # API routes
├── config/              # Django settings
│   ├── settings.py
│   └── urls.py
├── data/                # Static job dataset
│   └── jobs.json
├── frontend/src/        # TypeScript frontend
│   ├── main.ts
│   ├── api.ts
│   ├── types.ts
│   └── styles.css
├── scraper/             # Job scraping utility
│   └── scrape_jobs.py
├── templates/           # HTML templates
│   └── chat.html
├── static/dist/         # Built assets
├── manage.py
├── requirements.txt
├── package.json
└── .env
```

### Development Scripts

| Command                            | Description             |
| ---------------------------------- | ----------------------- |
| `npm run build:css`                | Compile Tailwind CSS    |
| `npm run build:js`                 | Bundle TypeScript       |
| `npm run build`                    | Build all assets        |
| `npm run typecheck`                | Run TypeScript compiler |
| `python manage.py runserver`       | Start dev server        |
| `python manage.py createsuperuser` | Create admin user       |

---

## Future Enhancements

### High Priority

- Real job application integration (LinkedIn, Indeed APIs)
- User authentication with saved profiles
- Email notifications for new matches
- Job alerts based on saved preferences

### Medium Priority

- Multi-resume support per user
- Analytics dashboard for application tracking
- Interview preparation resources
- Resume improvement suggestions

### Low Priority

- Mobile app version
- Voice interface support
- Multi-language resume parsing
- Company comparison features

---

## Support

For issues or questions:

1. Check `.env` configuration
2. Verify Gemini API key is valid
3. Review terminal logs for errors
4. Check database migrations are complete

---

## License

This project is for educational and demonstration purposes.
