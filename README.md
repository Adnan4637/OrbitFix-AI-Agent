# OrbitFix-AI

**AI-powered CI pipeline failure investigation agent built on GitLab Orbit.**

When a CI pipeline fails, OrbitFix-AI automatically traces the failure through GitLab Orbit's knowledge graph and generates a structured Root Cause and Impact Analysis Report — posted directly as a comment on the responsible merge request.

---

## The Problem

Most CI/CD tools tell you *what* failed. Developers still have to manually investigate:

- Which merge request introduced the regression
- Who authored that change
- Which files are directly affected
- Which other files depend on the changed code
- Whether to rollback or fix forward

This investigation can take longer than fixing the issue itself.

---

## The Solution

OrbitFix-AI combines GitLab REST API data, GitLab Orbit's relationship graph, and an LLM narrative layer to answer all of those questions automatically in seconds.

**What the agent determines:**

- The merge request that triggered the failing pipeline
- The author of that merge request
- The exact files changed in the MR
- The blast radius — all files that depend on the changed code
- A recommended action (rollback or fix)

---

## Why GitLab Orbit?

Traditional AI log analyzers only read text. GitLab Orbit provides a structured knowledge graph of relationships between source code, files, functions, classes, merge requests, pipelines, and developers.

OrbitFix-AI queries Orbit directly to traverse these relationships — replacing what would otherwise be dozens of manual API calls and hours of investigation.

---

## Demo

Pipeline `#2620919604` fails with:

```
ImportError: cannot import name 'UserService' from 'auth'
```

OrbitFix-AI produces:

```
Merge Request:  !1 — Rename UserService to AuthManager
Author:         m.adnan4637
Changed Files:  .gitlab/demo-project/auth.py
Blast Radius:   login.py, user_service.py, test_auth.py, test_login.py
Confidence:     100%
Action:         Rollback MR !1 or update all dependent imports
```

The full report is automatically posted as a comment on MR !1.

---

## How It Works

```
CI Pipeline Fails
        |
        v
Collect Pipeline Metadata       (GitLab REST API)
        |
        v
Collect Failed Job Log          (GitLab REST API)
        |
        v
Query Orbit — Root Cause        (Project → MR → Diff → Changed Files → Author)
        |
        v
Query Orbit — Blast Radius      (Changed File → Dependents)
        |
        v
Generate LLM Narrative          (Groq — Llama 3.1)
        |
        v
Build Structured Report
        |
        v
Post Report to MR               (GitLab REST API)
```

---

## Features

**Root Cause Detection** — Identifies the MR and commit that introduced the regression.

**Author Attribution** — Determines who made the change via Orbit's relationship graph.

**Changed File Analysis** — Lists every file modified in the responsible MR.

**Blast Radius Detection** — Finds all files that depend on the changed code.

**LLM Narrative** — Generates a concise human-readable summary of the failure.

**GitLab Integration** — Posts the complete report as a comment on the responsible MR.

---

## Technology Stack

- Python 3.11
- GitLab REST API
- GitLab Orbit Knowledge Graph
- Groq API (Llama 3.1 8B)
- `requests`, `python-dotenv`

---

## Project Structure

```
orbitfix-ai/
├── backend/
│   ├── config.py                   # Environment variables
│   ├── main.py                     # Main orchestrator
│   └── services/
│       ├── orbit_client.py         # GitLab Orbit REST queries
│       ├── gitlab_client.py        # GitLab REST API calls
│       ├── llm_service.py          # Groq LLM narrative generation
│       └── report_generator.py     # Markdown report builder
├── .gitlab/
│   └── demo-project/               # Demo regression codebase
│       ├── auth.py                 # AuthManager (renamed from UserService)
│       ├── login.py                # Still imports UserService — broken
│       ├── user_service.py         # Still imports UserService — broken
│       └── tests/
├── .gitlab-ci.yml                  # CI pipeline running pytest
├── .env.example                    # Environment variable template
├── requirements.txt
└── README.md
```

---

## Setup

**1. Clone the repository**

```bash
git clone https://gitlab.com/m.adnan4637-group/orbitfix-ai-dev.git
cd orbitfix-ai-dev
```

**2. Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy `.env.example` to `.env` and fill in your values:

```env
GITLAB_TOKEN=glpat-...
GITLAB_URL=https://gitlab.com
GITLAB_GROUP=your-group
GITLAB_PROJECT_PATH=your-group/your-project

LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.1-8b-instant
LLM_API_URL=https://api.groq.com/openai/v1/chat/completions

ORBIT_QUERY_LIMIT=20
```

**4. Run the agent**

```bash
python backend/main.py <project_path> <pipeline_id>
```

Example:

```bash
python backend/main.py m.adnan4637-group/orbitfix-ai-dev 2620919604
```

---

## Sample Report Output

```markdown
# Orbit Root Cause & Impact Analysis Report

Project:    m.adnan4637-group/orbitfix-ai-dev
Pipeline:   #2620919604
Generated:  2026-06-23 02:31 UTC

## Failure Source

| Field          | Value                                  |
|----------------|----------------------------------------|
| Merge Request  | !1 — Rename UserService to AuthManager |
| Author         | m.adnan4637                            |
| Commit         | e2242de9                               |
| Failed Job     | test                                   |

## AI Summary

The root cause is an ImportError caused by MR !1, which renamed
UserService to AuthManager in auth.py without updating the dependent
files login.py and user_service.py, which still import the old class name.

## Changed Files
- .gitlab/demo-project/auth.py

## Blast Radius (At Risk)
- .gitlab/demo-project/login.py
- .gitlab/demo-project/user_service.py
- .gitlab/demo-project/test_auth.py
- .gitlab/demo-project/test_login.py

## Confidence: 100%

## Recommended Action
Rollback MR !1 or update all dependent imports listed above.
```

---

## GitLab Orbit Queries Used

**Chain 1 — Root Cause:**
`Project → MergeRequest → MergeRequestDiff → MergeRequestDiffFile`
Finds which MR triggered the pipeline, who authored it, and which files it changed.

**Chain 2 — Blast Radius:**
`File → Definition → (reverse CALLS) → Definition → File`
Finds every file in the codebase that calls or imports anything from the changed file.

---

## GitLab Hackathon — Transcend 2026

Built for the GitLab Transcend Hackathon, Showcase Track.

This project demonstrates how GitLab Orbit's knowledge graph can power intelligent developer tooling that goes beyond log analysis to provide full causal understanding of CI failures.