# Development Workflow

## Purpose

This document describes how the Orbit Root Cause & Impact Analysis Agent will be developed, tested, and integrated throughout the project lifecycle.

The goal is to ensure that development follows a structured, milestone-driven approach and that every component can be validated independently before full system integration.

---

# Development Philosophy

The project follows a layered architecture:

```text
Data Collection
      ↓
Orbit Context Collection
      ↓
Relationship Analysis
      ↓
Root Cause Detection
      ↓
Impact Analysis
      ↓
Report Generation
      ↓
GitLab Integration
```

The AI model is intentionally placed near the end of the workflow.

The project's intelligence should primarily come from:

- GitLab Data
- Orbit Knowledge Graph
- Dependency Relationships

The LLM should be used to explain findings rather than discover them.

---

# Development Phases

## Phase 1 — Foundation Setup

### Objective

Prepare the repository structure and development environment.

### Deliverables

- GitLab Project
- Repository Structure
- Documentation
- Environment Configuration

### Files

```text
README.md
docs/problem-statement.md
docs/architecture.md
.env.example
requirements.txt
```

### Success Criteria

Project can be cloned and executed locally.

---

# Phase 2 — GitLab Data Collection

## Objective

Collect all information required for failure investigation.

### Components

```text
gitlab_client.py
log_collector.py
commit_collector.py
mr_collector.py
```

### Responsibilities

Collect:

- Pipeline Information
- Failed Jobs
- Job Logs
- Commit History
- Merge Requests
- Pipeline Metadata

### Example

Input:

```text
Project ID
Pipeline ID
```

Output:

```json
{
  "pipeline_id": 123,
  "status": "failed",
  "commit_sha": "abc123",
  "failed_job": "test",
  "failure_log": "ImportError"
}
```

### Success Criteria

Able to fetch pipeline and failure information directly from GitLab.

---

# Phase 3 — Orbit Integration

## Objective

Collect repository relationships from Orbit.

### Components

```text
orbit_client.py
```

### Responsibilities

Query Orbit for:

- File Relationships
- Dependencies
- Imports
- References
- Contributors
- Related Components

### Example Queries

```text
Which files depend on auth.py?
```

```text
Which files import UserService?
```

```text
Which functions call authenticate()?
```

### Success Criteria

Able to retrieve graph relationships from Orbit.

---

# Phase 4 — Root Cause Engine

## Objective

Determine the most probable source of a regression.

### Component

```text
root_cause_engine.py
```

### Inputs

```text
Pipeline Logs
Commits
Merge Requests
Orbit Relationships
```

### Example

Failure:

```text
ImportError: UserService
```

Recent Commit:

```text
Rename UserService → UserManager
```

Orbit Context:

```text
login.py still imports UserService
```

Result:

```text
Likely Root Cause:
Commit abc123 introduced a breaking rename.
```

### Success Criteria

System can generate a probable root-cause statement.

---

# Phase 5 — Impact Analysis

## Objective

Determine what else may be affected by the failure.

### Component

```text
impact_analyzer.py
```

### Analyze

- Affected Files
- Affected Functions
- Affected Services
- Affected Tests
- Affected Developers

### Example

```text
Changed File:
auth.py
```

Impact:

```text
login.py
user_service.py
admin_service.py

test_auth.py
test_login.py
```

### Success Criteria

Generate a dependency impact report.

---

# Phase 6 — AI Reasoning Layer

## Objective

Convert collected evidence into a developer-friendly explanation.

### Component

```text
llm_service.py
```

### Model

```text
Llama 3.1 (Ollama)
```

### Inputs

```text
Logs
Commits
MRs
Orbit Results
Impact Analysis
```

### Outputs

```text
Human-readable explanation
Confidence score
Recommended action
```

### Success Criteria

Generate clear investigation summaries.

---

# Phase 7 — Report Generation

## Objective

Create structured investigation reports.

### Component

```text
report_generator.py
```

### Output Example

```markdown
# Root Cause Report

Pipeline:
123

Root Cause:
Commit abc123

Related MR:
!42

Author:
Ahmed Ali Khan

Affected Files:
- auth.py
- login.py

Affected Tests:
- test_auth.py

Recommendation:
Rollback commit abc123
```

### Success Criteria

Generate downloadable markdown reports.

---

# Phase 8 — GitLab Integration

## Objective

Publish investigation results directly into GitLab.

### Components

```text
comment_publisher.py
webhook.py
```

### Actions

- Create MR Comments
- Create Issue Comments
- Attach Reports
- Trigger Analysis Automatically

### Success Criteria

Results appear directly inside GitLab.

---

# Testing Strategy

## Unit Testing

Validate:

- GitLab API Calls
- Orbit Queries
- Root Cause Engine
- Impact Analysis

### Directory

```text
tests/
```

---

## Integration Testing

Workflow:

```text
Fail Pipeline
      ↓
Webhook Trigger
      ↓
Collect Data
      ↓
Orbit Query
      ↓
Analysis
      ↓
Report
```

---

# Demo Scenario

## Simulated Failure

Developer changes:

```python
UserService
```

to

```python
UserManager
```

without updating dependent imports.

Pipeline fails:

```text
ImportError
```

Agent automatically:

1. Detects failure.
2. Finds responsible commit.
3. Identifies related MR.
4. Calculates impacted files.
5. Generates Root Cause Report.
6. Posts findings to GitLab.

---

# MVP Scope

The MVP focuses on:

✅ CI Pipeline Failures

✅ Commit Attribution

✅ Merge Request Attribution

✅ Orbit Relationship Analysis

✅ Impact Analysis

✅ GitLab Reporting

---

# Out of Scope (Hackathon MVP)

❌ Kubernetes Analysis

❌ Production Incident Analysis

❌ Deployment Failures

❌ Multi-Repository Dependency Graphs

❌ Security Vulnerability Investigation

These can be future enhancements after the hackathon.