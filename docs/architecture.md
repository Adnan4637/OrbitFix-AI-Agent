# System Architecture

## High Level Flow

Pipeline Failure
        │
        ▼
GitLab Webhook
        │
        ▼
GitLab Data Collector
        │
        ├── Pipeline Details
        ├── Failed Job Logs
        ├── Recent Commits
        └── Related Merge Requests
        │
        ▼
Orbit Query Engine
        │
        ├── File Relationships
        ├── Dependencies
        ├── Contributors
        └── References
        │
        ▼
Root Cause Engine
        │
        ▼
Impact Analyzer
        │
        ▼
Report Generator
        │
        ▼
GitLab Comment / Issue / MR