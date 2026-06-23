# OrbitFix-AI — Full Project Documentation

## What We Are Building

**OrbitFix-AI** is an AI-powered CI pipeline failure investigation agent built on top of **GitLab Orbit** — GitLab's knowledge graph that maps relationships between code, files, functions, merge requests, pipelines, developers, and dependencies.

When a CI pipeline fails, most tools tell you *what* failed. OrbitFix-AI tells you:
- *Why* it failed (which code change introduced it)
- *Who* introduced it (which developer, which MR)
- *What else is at risk* (which other files depend on the changed code)

---

## The Problem We Are Solving

A typical developer's manual investigation after a pipeline failure:

1. Open the failed pipeline
2. Read the job logs
3. Look at recent commits
4. Open each merge request
5. Check which files changed
6. Manually trace which other files import or call those changed files
7. Decide whether to rollback or fix

This process takes **minutes to hours** depending on repository size. OrbitFix-AI compresses it into **seconds** by querying GitLab Orbit's pre-indexed relationship graph instead of doing all of this manually.

---

## How It Is Different From Existing Tools

| Capability | Regular CI Tools | OrbitFix-AI |
|---|---|---|
| Read job logs | Yes | Yes |
| Explain the error | Yes | Yes |
| Find responsible commit | No | Yes |
| Find responsible MR | No | Yes |
| Identify author | No | Yes |
| Blast radius detection | No | Yes |
| Orbit relationship analysis | No | Core feature |

---

## The Complete Flow

```
Pipeline Failure Event
        │
        ▼
Step 1: Collect GitLab Metadata
        GitLab REST API
        - Pipeline details (status, commit SHA, branch)
        - Failed jobs (which job failed)
        - Job log (the actual error message)
        │
        ▼
Step 2: Query Orbit — Chain 1 (Root Cause)
        GitLab Orbit Knowledge Graph
        - Find MR that triggered the pipeline
        - Find who authored that MR
        - Find which files changed in that MR
        │
        ▼
Step 3: Query Orbit — Chain 2 (Blast Radius)
        GitLab Orbit Knowledge Graph
        - For each changed file, find its definitions (functions/classes)
        - Find every other definition that calls those definitions
        - Find which files those callers live in
        - These are the "at risk" files
        │
        ▼
Step 4: Generate LLM Summary
        Groq API (Llama 3.1)
        - Pass all structured evidence to the LLM
        - LLM writes a 3-5 sentence human-readable narrative
        - Intelligence comes from Orbit — LLM only writes the summary
        │
        ▼
Step 5: Build Report
        report_generator.py
        - Structured markdown report with all findings
        - Confidence score based on evidence quality
        - Recommended action (rollback or fix)
        │
        ▼
Step 6: Publish to GitLab
        GitLab REST API
        - Post report as a comment on the MR that caused the failure
        - Developer sees it immediately in their workflow
```
GitLab Pipeline Failure
           |
           v
Webhook Listener
           |
           v
GitLab API Collector
           |
           v
Orbit Query Engine
           |
           v
Root Cause Engine
           |
           v
Impact Analyzer
           |
           v
Report Generator
           |
           v
GitLab Comment

---

## Architecture

```
orbitfix-ai/
├── backend/
│   ├── config.py              # Environment variables and settings
│   ├── main.py                # Orchestrator — wires all services together
│   └── services/
│       ├── orbit_client.py    # Queries GitLab Orbit knowledge graph
│       ├── gitlab_client.py   # Calls GitLab REST API
│       ├── llm_service.py     # Calls Groq API for narrative summary
│       └── report_generator.py # Builds the final markdown report
│
├── .gitlab/
│   └── demo-project/          # Demo "victim" codebase for testing
│       ├── auth.py            # Contains UserService / AuthManager class
│       ├── login.py           # Imports from auth.py
│       ├── user_service.py    # Imports from auth.py
│       └── tests/
│           ├── test_auth.py
│           └── test_login.py
│
├── .gitlab-ci.yml             # CI pipeline that runs pytest on demo-project
├── .env                       # API keys and configuration (never committed)
└── requirements.txt           # Python dependencies
```

---

## How Each API Is Used

### 1. GitLab REST API

**Purpose:** Collect raw pipeline metadata — the "what happened" data before Orbit adds context.

**Authentication:** Personal Access Token (`glpat-...`) with `api` + `write_repository` scopes, passed as `PRIVATE-TOKEN` header.

**Key endpoints used:**

```
GET /api/v4/projects/{project_id}/pipelines/{pipeline_id}
    → Gets pipeline status, commit SHA, branch name

GET /api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs
    → Lists all jobs; we filter for status=failed

GET /api/v4/projects/{project_id}/jobs/{job_id}/trace
    → Gets the raw job log text (last 5000 chars)

GET /api/v4/projects/{project_id}/merge_requests
    → Gets recent merged MRs for fallback context

POST /api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes
    → Posts the final report as a comment on the MR
```

**File:** `backend/services/gitlab_client.py`

---

### 2. GitLab Orbit Knowledge Graph

**Purpose:** The core differentiator. Orbit provides a pre-indexed graph of relationships between every entity in the GitLab SDLC — files, functions, commits, MRs, pipelines, developers, dependencies. One query replaces dozens of manual API calls.

**Authentication:** Uses `glab` CLI which is already authenticated via the same GitLab token.

**How queries work:** JSON traversal queries sent via `glab orbit remote query -`, piped from Python via `subprocess`.

```python
subprocess.run(
    ["glab", "orbit", "remote", "query", "-", "--format", "raw"],
    input=json.dumps(query),
    capture_output=True,
    text=True
)
```

**Chain 1 — Root Cause Query:**

Traverses: `Project → MergeRequest → MergeRequestDiff → MergeRequestDiffFile`

Edges used:
- `IN_PROJECT` (MergeRequest → Project)
- `HAS_LATEST_DIFF` (MergeRequest → MergeRequestDiff)
- `HAS_FILE` (MergeRequestDiff → MergeRequestDiffFile)

Also: `AUTHORED` (User → MergeRequest) for author attribution.

Result: Which MR triggered the pipeline, who wrote it, which files it changed.

**Chain 2 — Blast Radius Query:**

Traverses: `File → Definition → (reverse CALLS) → Definition → File`

Edges used:
- `IN_PROJECT` (File → Project)
- `DEFINES` (File → Definition)
- `CALLS` (Definition → Definition, walked in reverse)
- `DEFINES` (File → Definition, walked in reverse)

Result: Every file in the codebase that calls or imports anything from the changed file — these are at risk of breaking too.

**File:** `backend/services/orbit_client.py`

---

### 3. Groq API (Llama 3.1)

**Purpose:** Generate a concise, human-readable narrative summary from the structured evidence collected by Orbit and GitLab. The LLM does not perform analysis — it only writes prose around what Orbit already determined.

**Authentication:** Groq API key (`gsk_...`) passed as `Authorization: Bearer` header.

**Endpoint:** `POST https://api.groq.com/openai/v1/chat/completions`

**Model:** `llama-3.1-8b-instant` (fast, free tier available)

**Request format** (OpenAI-compatible):

```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "user",
      "content": "You are an expert software engineer analyzing a CI pipeline failure. Evidence: [failure log, changed files, blast radius, MR title, author]. Write a 3-5 sentence root cause summary."
    }
  ],
  "max_tokens": 400,
  "temperature": 0.3
}
```

**Why Groq instead of others:** Free, fast (sub-second responses), no credit card needed, OpenAI-compatible format works out of the box.

**File:** `backend/services/llm_service.py`

---

## The Demo Regression

To demonstrate the agent, we created a controlled regression in the demo project:

**Baseline (working):**
```python
# auth.py
class UserService:
    def authenticate(self, username, password): ...
    def create_user(self, username, password): ...

# login.py
from auth import UserService   # works fine

# user_service.py
from auth import UserService   # works fine
```

**Regression (broken — MR !1):**
```python
# auth.py — UserService renamed to AuthManager
class AuthManager:             # renamed without telling dependents
    ...

# login.py — still imports old name
from auth import UserService   # ImportError: cannot import name 'UserService'

# user_service.py — still imports old name
from auth import UserService   # ImportError: cannot import name 'UserService'
```

**What the CI failure shows:**
```
ImportError: cannot import name 'UserService' from 'auth'
```

**What OrbitFix-AI adds:**
- This error came from MR !1 (Rename UserService to AuthManager)
- Author: Adnan Rasheed
- Changed file: auth.py
- Blast radius: login.py and user_service.py both depend on UserService from auth.py

---

## Orbit Schema Entities Used

From the full Orbit schema (28 entity types), OrbitFix-AI uses:

| Entity | Domain | Purpose |
|---|---|---|
| Project | core | Scoping all queries to one project |
| MergeRequest | code_review | Finding what triggered the pipeline |
| MergeRequestDiff | code_review | Getting the diff snapshot |
| MergeRequestDiffFile | code_review | Getting changed file paths |
| User | core | Getting the MR author |
| File | source_code | Finding changed files and their dependents |
| Definition | source_code | Finding functions/classes and their callers |
| Pipeline | ci | Connecting the failure back to the MR |

---

## Sample Output Report

```markdown
# Orbit Root Cause & Impact Analysis Report

Project: m.adnan4637-group/orbitfix-ai-dev
Pipeline: #2620919604
Generated: 2026-06-22 19:00 UTC

## Failure Source

| Field       | Value                              |
|-------------|------------------------------------|
| Merge Request | !1 — Rename UserService to AuthManager |
| Author      | m.adnan4637                        |
| Commit      | e2242de9                           |
| Failed Job  | test                               |

## Evidence

Failure Log:
ImportError: cannot import name 'UserService' from 'auth'

AI Summary:
The failure was introduced by MR !1 which renamed UserService
to AuthManager in auth.py without updating login.py and
user_service.py, which still import the old class name.

## Changed Files (MR !1)
- auth.py

## Impact Analysis (Blast Radius)
- login.py (imports UserService from auth)
- user_service.py (imports UserService from auth)

## Confidence: 90%

## Recommended Action
Rollback MR !1 or update all dependent imports listed above.
```

---

## Current Status

- GitLab project created and linked: `m.adnan4637-group/orbitfix-ai-dev`
- Orbit enabled on `m.adnan4637-group` group (36 entities indexed)
- Demo regression committed and MR !1 created
- CI pipeline failing as expected (pipeline #2620919604)
- Backend Python agent running end-to-end
- GitLab REST API collecting real pipeline/job/log data
- Orbit queries returning data for project (MR indexing in progress)
- Groq LLM generating summaries
- Report generation working

**Next steps:**
- Confirm Orbit has indexed MR !1 relationships (may need a few more minutes)
- Run agent against pipeline #2620919604 to get full report with MR/author/blast-radius
- Push all backend code to GitLab
- Publish to AI Catalog for hackathon submission