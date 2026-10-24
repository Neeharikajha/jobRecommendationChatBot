# AI Job Chat Assistant

A conversational AI-powered job matching and application assistant built with Django, Google Gemini, and TypeScript.

## Project Overview

This is a multi-agent system that:

1. **Parses resumes** (PDF/DOCX) using AI to extract structured data
2. **Recommends jobs** from a dataset based on resume skills/experience
3. **Applies to jobs** on user request and tracks applications
4. **Converses naturally** to refine search results with filters

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (TypeScript)                   │
│  • React-like UI for resume upload & chat               │
│  • API client for backend calls                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Django REST Backend                         │
│  • UploadView: Resume parsing & storage                 │
│  • ChatView: Message handling & routing                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│          Multi-Agent System (agents/)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Orchestrator Agent                               │  │
│  │ • Manages conversation flow                      │  │
│  │ • Routes to tool calls (Gemini Auto Functions)   │  │
│  └──────────────────────────────────────────────────┘  │
│         ↓         ↓         ↓         ↓                 │
│    ┌────────┬──────────┬──────────┬──────────┐         │
│    │ Resume │  Search  │  Get Job │  Apply   │         │
│    │ Parser │  Jobs    │ Details  │ to Job   │         │
│    └────────┴──────────┴──────────┴──────────┘         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│            Data Layer                                    │
│  • SQLite (dev) / PostgreSQL (prod)                     │
│  • Resume, Message, Application models                 │
│  • JSON job dataset (1500+ jobs)                        │
└─────────────────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 16+
- Google Gemini API key (get free at [Google AI Studio](https://aistudio.google.com/app/apikey))

### 1. Clone and Install

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 2. Environment Setup

Create `.env` file (already partially configured):

```
GEMINI_API_KEY=your_key_here
SECRET_KEY=your-long-random-string-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional, for admin panel)
python manage.py createsuperuser
```

### 4. Build Frontend

```bash
# Compile TypeScript and CSS
npm run build

# Or watch for changes during development
npm run build:js &
npm run build:css &
```

### 5. Run the Application

```bash
# Start Django dev server
python manage.py runserver

# Open in browser
# http://localhost:8000
```

## How to Use

1. **Upload Resume**: Click 📎 and select a PDF or DOCX file
2. **View Parsed Data**: Assistant displays extracted name, skills, experience
3. **Browse Jobs**: Assistant recommends 10 matching jobs with match reasons
4. **Refine Search**: Type "show only remote roles" or "jobs requiring React"
5. **Apply**: Type "apply to job 3" to record an application
6. **Track**: Type "show my applied jobs" to see application history

## API Endpoints

| Endpoint       | Method | Description                         |
| -------------- | ------ | ----------------------------------- |
| `/api/upload/` | POST   | Upload resume (multipart/form-data) |
| `/api/chat/`   | POST   | Send message to agent               |

## Tool Declarations

The orchestrator agent has access to these tools:

- `search_jobs(remote, skills, location, keyword, limit)` - Find matching jobs
- `get_job_details(job_id)` - Get full job info
- `apply_to_job(job_id)` - Record application
- `get_applications()` - List user's applications

## Data Models

```python
Resume
  - session_key (unique per user)
  - data (JSON: parsed resume fields)
  - created_at

Application
  - session_key
  - job_id
  - job_title, company
  - applied_at
  - status
  - (unique constraint: session_key + job_id)

Message
  - session_key
  - role ("user" or "model")
  - content (text)
  - created_at
```

## Dataflow

```
User Upload Resume
    ↓
extract_text() → parse_resume() → Gemini JSON extraction
    ↓
Resume model stored in DB
    ↓
User Message (search/apply request)
    ↓
Orchestrator Agent receives message + resume context
    ↓
Gemini decides which tool to call
    ↓
Tool executes (search, apply, get details, etc.)
    ↓
Tool returns result
    ↓
Gemini generates conversational response
    ↓
Response sent to user
```

## Project Structure

```
hidani-job-assistant/
├── agents/                 # Multi-agent system
│   ├── orchestrator.py    # Main agent coordinator
│   ├── llm.py             # Gemini client & JSON generation
│   ├── resume_parser.py   # PDF/DOCX parsing
│   ├── matcher.py         # Job search & matching logic
│   ├── tools.py           # Tool implementations
│   ├── prompts.py         # System prompts
│   └── __init__.py
├── chat/                   # Django app
│   ├── models.py          # Resume, Application, Message
│   ├── views.py           # API views
│   ├── urls.py            # API routes
│   └── ...
├── config/                 # Django settings
│   ├── settings.py        # Main config
│   ├── urls.py            # URL routing
│   └── wsgi.py
├── frontend/src/          # TypeScript frontend
│   ├── main.ts            # Chat UI logic
│   ├── api.ts             # API client
│   ├── types.ts           # TypeScript interfaces
│   └── styles.css         # Tailwind styles
├── data/
│   └── jobs.json          # Job dataset (1500+ jobs)
├── templates/
│   └── chat.html          # Main HTML template
├── static/
│   └── dist/              # Built JS & CSS (after npm run build)
├── manage.py              # Django CLI
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
└── README.md
```

## Troubleshooting

### "GEMINI_API_KEY not set"

- Check `.env` file exists in project root
- Verify key is correctly copied from Google AI Studio
- Restart server after updating `.env`

### "Module not found" errors

- Run `pip install -r requirements.txt`
- Run `npm install`

### Frontend not loading

- Run `npm run build` to compile TypeScript/CSS
- Check that `static/dist/` contains `main.js` and `styles.css`

### Resume parsing fails

- Ensure file is text-based PDF (not scanned image)
- Try DOCX format if PDF fails
- Max file size is 5MB

### No jobs matching

- Try searching by keyword (e.g., "engineer", "remote")
- Dataset may not have jobs for very specific combinations
- Adjust filters and try again

## Deployment

### Render.com (Free tier)

```bash
# Push to GitHub, connect to Render
# Build command: pip install -r requirements.txt && npm install && npm run build && python manage.py migrate
# Start command: gunicorn config.wsgi:application

# Set environment variables in Render dashboard
GEMINI_API_KEY=xxx
SECRET_KEY=xxx
DEBUG=False
ALLOWED_HOSTS=yourdomain.onrender.com
```

## Technologies Used

### Backend

- **Django 4.2** - Web framework
- **Django REST Framework** - API
- **Google Genai** - Gemini LLM
- **SQLite / PostgreSQL** - Database
- **pdfplumber** - PDF parsing
- **python-docx** - DOCX parsing
- **rapidfuzz** - Fuzzy string matching

### Frontend

- **TypeScript** - Type-safe JS
- **Tailwind CSS** - Styling
- **esbuild** - Bundler

### DevOps

- **Gunicorn** - Production server
- **WhiteNoise** - Static file serving
- **dj-database-url** - Database config

## API Keys & Secrets

⚠️ **Never commit `.env` file or expose API keys!**

- Get Gemini API key: [Google AI Studio](https://aistudio.google.com/app/apikey)
- Generate SECRET_KEY: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## Performance Notes

- Jobs dataset: 1500+ cached in memory (LRU cache)
- Resume parsing: ~2-3 seconds per file
- Job search: <200ms
- Agent thinking: ~1-5 seconds (depends on Gemini API)
- Session-based identification: No login required, uses Django session cookies

## Next Steps & TODOs

- [ ] Add real job application APIs (email or third-party integrations)
- [ ] Support more resume formats (TXT, etc.)
- [ ] Add user authentication & saved profiles
- [ ] Integrate with LinkedIn API
- [ ] Add job alerts & notifications
- [ ] Support multiple resume uploads per user
- [ ] Analytics dashboard for applications
- [ ] Rate limiting for API calls

---

**For support or issues**: Check logs in terminal, review `.env` setup, verify API keys.
# jobRecommendationChatBot
