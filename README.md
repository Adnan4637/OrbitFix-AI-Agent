# OrbitFix-AI
## Overview

Orbit Root Cause & Impact Analysis Agent is an AI-powered developer assistant built on top of GitLab Orbit.

When a CI pipeline fails, developers often spend significant time investigating:

- Which commit introduced the failure
- Which merge request caused it
- Which files are impacted
- Which services are affected
- Whether a rollback is required

Our agent automatically traces a failure through GitLab Orbit's knowledge graph and generates a structured root-cause and impact report.

---

## Problem Statement

Most CI/CD tools and AI assistants can explain **what failed**.

However, developers still need to manually investigate:

- Where the failure originated
- Who introduced the change
- What else may break because of it
- Which teams or services are impacted

This investigation can take significantly longer than fixing the actual issue.

---

## Solution

Orbit Root Cause & Impact Analysis Agent combines:

- GitLab Pipeline Data
- Job Logs
- Commits
- Merge Requests
- GitLab Orbit Knowledge Graph
- AI Reasoning

to automatically determine:

- Probable root cause
- Related commit
- Related merge request
- Affected files
- Affected components
- Blast radius / impact

---

## Why GitLab Orbit?

Traditional AI log analyzers only read text logs.

GitLab Orbit provides a structured graph of relationships between:

- Source Code
- Files
- Functions
- Classes
- Merge Requests
- Pipelines
- Developers
- Dependencies

Using Orbit allows the agent to move beyond log analysis and understand how code changes relate to failures across the software delivery lifecycle.

---

## Example Output

```text
Root Cause Analysis Report

Failure Source:
MR !42

Commit:
abc123

Author:
Ahmed Ali Khan

Affected Files:
- auth.py
- login.py

Affected Components:
- Authentication Service
- User API

Impacted Tests:
- test_auth.py
- test_login.py

Confidence:
89%

Recommendation:
Rollback commit abc123 or update dependent imports.
```

---

## Workflow

```text
Pipeline Failure
        │
        ▼
Collect Logs
        │
        ▼
Collect GitLab Metadata
        │
        ▼
Query Orbit Knowledge Graph
        │
        ▼
Identify Root Cause
        │
        ▼
Analyze Impact Radius
        │
        ▼
Generate Investigation Report
        │
        ▼
Publish Results to GitLab
```

---

## Features

### Root Cause Detection

Identify the most likely source of a regression.

### Commit Attribution

Determine which commit introduced the issue.

### Merge Request Attribution

Trace failures back to merge requests.

### Impact Analysis

Estimate affected files, services and tests.

### Blast Radius Detection

Understand the broader consequences of a failure.

### GitLab Integration

Post findings directly back into GitLab workflows.

---

## Technology Stack

- Python 3.11+
- FastAPI
- GitLab REST API
- GitLab Orbit
- Ollama
- Llama 3.1
- GitLab Duo Agent Platform

---

## Project Structure

```text
orbit-root-cause-agent/

backend/
docs/
sample-data/
tests/

README.md
requirements.txt
.env.example
```

---

## Current Status

🚧 Hackathon MVP in development

Planned MVP capabilities:

- Pipeline failure ingestion
- GitLab metadata collection
- Orbit relationship queries
- Root cause analysis
- Impact analysis report generation

