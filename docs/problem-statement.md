# Problem Statement

## Background

Modern software teams rely heavily on CI/CD pipelines to validate code changes before deployment. While GitLab provides excellent visibility into pipeline status, developers still spend significant time investigating failures after they occur.

A failed pipeline tells developers **what failed**, but rarely explains:

- Which code change introduced the issue
- Which merge request is responsible
- Which components are impacted
- Which services may be affected next
- Whether the issue is isolated or part of a larger regression

As repositories grow and development becomes more distributed, identifying the true source of a failure becomes increasingly difficult.

---

## The Challenge

When a CI pipeline fails, developers often perform a manual investigation process:

1. Review pipeline logs
2. Inspect recent commits
3. Examine merge requests
4. Analyze changed files
5. Trace dependencies
6. Identify impacted components
7. Determine whether rollback is required

This process can take anywhere from several minutes to several hours depending on repository size and complexity.

The investigation effort frequently exceeds the time required to implement the actual fix.

---

## Existing Limitations

Current CI troubleshooting approaches primarily focus on:

- Log analysis
- Error explanation
- Configuration validation
- Pipeline optimization

While these approaches help explain the failure itself, they often do not provide sufficient context about:

- Failure origin
- Change attribution
- Dependency impact
- Repository-wide consequences

Developers are still responsible for manually connecting information across commits, merge requests, files, pipelines, and dependencies.

---

## Proposed Solution

### Orbit Root Cause & Impact Analysis Agent

Orbit Root Cause & Impact Analysis Agent uses GitLab Orbit's knowledge graph to investigate pipeline failures beyond simple log analysis.

The agent combines:

- Pipeline metadata
- Job execution logs
- Commit history
- Merge request activity
- Code relationships
- Dependency mappings
- Orbit graph context

to automatically generate a structured investigation report.

The report identifies:

- Probable root cause
- Related commit
- Related merge request
- Contributing developer
- Affected files
- Impacted components
- Potential blast radius
- Recommended next actions

---

## Why GitLab Orbit?

GitLab Orbit provides a structured, queryable representation of the software development lifecycle.

Unlike traditional log analyzers, Orbit understands relationships between:

- Source files
- Functions and classes
- Commits
- Merge requests
- Pipelines
- Dependencies
- Contributors

This contextual understanding enables more accurate root-cause attribution and impact analysis.

---

## Expected Outcome

By automatically tracing failures through the Orbit knowledge graph, the agent helps developers:

- Reduce investigation time
- Identify regressions faster
- Understand dependency impact
- Improve incident response
- Make more informed rollback decisions

Ultimately, the goal is to transform pipeline failures from a manual investigation exercise into an actionable, data-driven workflow.

---

## Hackathon Goal

Build an Orbit-powered AI agent that can:

1. Detect a failed pipeline.
2. Collect relevant GitLab and Orbit context.
3. Identify the most likely source of the regression.
4. Analyze affected components and dependencies.
5. Generate a structured Root Cause & Impact Report.
6. Publish the findings back into the GitLab workflow.

This demonstrates how GitLab Orbit can be used not only to understand code, but also to understand the relationships and consequences of changes across the software development lifecycle.
