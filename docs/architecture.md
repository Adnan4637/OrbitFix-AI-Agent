# OrbitFix-AI — Architecture & Technical Documentation

## What OrbitFix-AI Does

OrbitFix-AI is an AI-powered CI pipeline failure investigation agent built on GitLab Orbit. When a CI pipeline fails, the agent automatically:

1. Collects pipeline metadata and job logs via GitLab REST API
2. Queries GitLab Orbit to find which MR caused the failure, who authored it, and which files changed
3. Analyzes the blast radius — all files that depend on the changed code
4. Generates a structured Root Cause and Impact Analysis Report
5. Posts the report as a comment on the responsible MR

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

## Complete Agent Flow

```
CI Pipeline Fails
        |
        v
Step 1: Collect GitLab Metadata          (gitlab_client.py)
        - Pipeline details (status, commit SHA, branch)
        - Failed jobs list
        - Raw job log (last 5000 chars)
        |
        v
Step 2: Query Orbit — Root Cause         (orbit_client.py)
        - Traversal: Project → MR → MergeRequestDiff → MergeRequestDiffFile
        - Separate traversal: Project → MR → User (author)
        - Returns: MR title, MR iid, author username, changed file paths
        |
        v
Step 3: Blast Radius Analysis            (main.py + gitlab_client.py)
        - Filters changed files to demo-project Python files only
        - Uses GitLab REST MR changes endpoint to find dependent files
        - Returns: all files at risk of breaking
        |
        v
Step 4: Generate LLM Narrative           (llm_service.py)
        - Extracts error lines from job log
        - Sends structured evidence to Groq (Llama 3.1)
        - Returns: 3-5 sentence human-readable root cause summary
        |
        v
Step 5: Build Report                     (report_generator.py)
        - Structured markdown with all findings
        - Confidence score based on evidence quality
        - Recommended action (rollback or fix forward)
        |
        v
Step 6: Post to GitLab                   (gitlab_client.py)
        - Posts report as a note on the responsible MR
        - Developer sees it immediately in their workflow
```

---

## Project Structure

```
orbitfix-ai/
├── backend/
│   ├── config.py                   # Loads environment variables via dotenv
│   ├── main.py                     # Main orchestrator — wires all services
│   └── services/
│       ├── orbit_client.py         # GitLab Orbit REST API queries
│       ├── gitlab_client.py        # GitLab REST API calls
│       ├── llm_service.py          # Groq API (Llama 3.1) narrative generation
│       └── report_generator.py     # Builds final markdown report
├── .gitlab/
│   └── demo-project/               # Demo regression codebase
│       ├── auth.py                 # AuthManager (renamed from UserService)
│       ├── login.py                # Still imports UserService — broken
│       ├── user_service.py         # Still imports UserService — broken
│       └── tests/
│           ├── test_auth.py
│           └── test_login.py
├── .gitlab-ci.yml                  # Runs pytest on demo-project
├── .env                            # API keys (never committed)
├── .env.example                    # Template for environment variables
├── requirements.txt
└── README.md
```

---

## API Integrations

### 1. GitLab REST API

Handles all raw data collection and report publishing.

**Authentication:** Personal Access Token (`glpat-...`) with `api` and `write_repository` scopes, passed as `PRIVATE-TOKEN` header.

**Endpoints used:**

```
GET  /api/v4/projects/{encoded_path}
     → Resolves project path to numeric project ID

GET  /api/v4/projects/{id}/pipelines/{pipeline_id}
     → Pipeline status, commit SHA, branch

GET  /api/v4/projects/{id}/pipelines/{pipeline_id}/jobs
     → All jobs; filtered for status=failed

GET  /api/v4/projects/{id}/jobs/{job_id}/trace
     → Raw job log text (last 5000 chars)

GET  /api/v4/projects/{id}/merge_requests/{mr_iid}/changes
     → All files changed in a specific MR

POST /api/v4/projects/{id}/merge_requests/{mr_iid}/notes
     → Posts the final report as a comment on the MR
```

**File:** `backend/services/gitlab_client.py`

---

### 2. GitLab Orbit Knowledge Graph

The core differentiator. Orbit provides a pre-indexed graph of relationships between every entity in the GitLab SDLC.

**Authentication:** GitLab Personal Access Token passed as `Authorization: Bearer` header.

**Endpoint:** `POST https://gitlab.com/api/v4/orbit/query`

**Response structure:**
```json
{
  "result": {
    "nodes": [...],
    "edges": [...]
  },
  "query_type": "traversal",
  "row_count": N
}
```

Note: Orbit wraps its response in a `result` key. The agent unwraps this before processing nodes.

**Chain 1 — Root Cause Traversal:**

```
Project → MergeRequest → MergeRequestDiff → MergeRequestDiffFile
```

Relationships traversed:
- `IN_PROJECT` (MergeRequest → Project)
- `HAS_LATEST_DIFF` (MergeRequest → MergeRequestDiff)
- `HAS_FILE` (MergeRequestDiff → MergeRequestDiffFile)

Separate author query:
```
Project → MergeRequest → User
```
- `IN_PROJECT` (MergeRequest → Project)
- `AUTHORED` (User → MergeRequest)

Result: MR title, iid, author username, list of changed file paths.

**Chain 2 — Blast Radius Traversal:**

```
File → Definition → (reverse CALLS) → Definition → File
```

Relationships traversed:
- `IN_PROJECT` (File → Project)
- `DEFINES` (File → Definition)
- `CALLS` (Definition → Definition)
- `DEFINES` (File → Definition, reverse)

Result: All files whose definitions call or import anything from the changed file.

**Orbit entities used:**

| Entity | Domain | Purpose |
|---|---|---|
| Project | core | Scope all queries to one project |
| MergeRequest | code_review | Find what triggered the pipeline |
| MergeRequestDiff | code_review | Get the diff snapshot |
| MergeRequestDiffFile | code_review | Get changed file paths |
| User | core | Get MR author |
| File | source_code | Find changed files and dependents |
| Definition | source_code | Find functions/classes and callers |

**File:** `backend/services/orbit_client.py`

---

### 3. Groq API (Llama 3.1)

Generates a concise human-readable narrative from the structured evidence. The LLM does not perform analysis — it only writes prose around what Orbit and GitLab already determined.

**Authentication:** Groq API key passed as `Authorization: Bearer` header.

**Endpoint:** `POST https://api.groq.com/openai/v1/chat/completions`

**Model:** `llama-3.1-8b-instant`

**Prompt strategy:** Only error lines from the job log are passed (filtered by keywords: Error, ImportError, Exception, FAILED). This prevents the LLM from summarizing irrelevant log noise like pip warnings.

**File:** `backend/services/llm_service.py`

---

## The Demo Regression

A controlled regression in `.gitlab/demo-project/` demonstrates the agent end-to-end.

**Baseline branch (`add-demo-auth-module`) — passing:**
```python
# auth.py
class UserService:
    def authenticate(self, username, password): ...
    def create_user(self, username, password): ...

# login.py
from auth import UserService    # works

# user_service.py
from auth import UserService    # works
```

**Regression branch (`introduce-regression`) — MR !1 — failing:**
```python
# auth.py — class renamed without updating dependents
class AuthManager:
    ...

# login.py — still imports old name
from auth import UserService    # ImportError

# user_service.py — still imports old name
from auth import UserService    # ImportError
```

**CI failure:**
```
ImportError: cannot import name 'UserService' from 'auth'
ERROR tests/test_auth.py
ERROR tests/test_login.py
```

**What OrbitFix-AI produces:**
- MR !1 identified as the source
- Author: m.adnan4637
- Changed file: `.gitlab/demo-project/auth.py`
- Blast radius: `login.py`, `user_service.py`, `test_auth.py`, `test_login.py`
- Confidence: 100%
- Action: Rollback MR !1 or update all dependent imports

---

## Confidence Score Calculation

The confidence score is calculated based on available evidence:

| Evidence | Points |
|---|---|
| Base score | 50 |
| MR identified | +20 |
| Changed files found | +10 |
| Blast radius detected | +10 |
| Job log collected | +10 |
| Maximum | 100 |

---

## Current Status

- GitLab project: `m.adnan4637-group/orbitfix-ai-dev`
- Orbit enabled and indexing on group `m.adnan4637-group`
- Demo regression: MR !1 open, CI pipeline #2620919604 failing
- Backend agent: fully operational end-to-end
- GitLab REST API: collecting real pipeline, job, and log data
- Orbit REST API: returning MR, author, and changed file data
- Blast radius: detected via MR diff analysis
- Groq LLM: generating accurate root cause summaries
- Report posting: confirmed working on MR !1