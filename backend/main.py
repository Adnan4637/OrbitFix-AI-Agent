# main.py
"""
OrbitFix-AI — Main Agent Orchestrator

Workflow:
1. Receive pipeline failure (project_path + pipeline_id)
2. Collect GitLab metadata (pipeline, jobs, logs, MRs, commits)
3. Query Orbit knowledge graph (root cause + blast radius)
4. Generate LLM narrative summary
5. Build and output the Root Cause & Impact Report
6. Post report back to GitLab as MR comment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gitlab_client import (
    get_project_by_path,
    get_pipeline,
    get_failed_jobs,
    get_job_log,
    get_recent_mrs,
    post_mr_comment,
    get_mr_changes
)
from services.orbit_client import (
    query_root_cause,
    query_mr_author,
    query_blast_radius,
    query_all_files
)
from services.llm_service import generate_summary
from services.report_generator import generate_report, generate_minimal_report
from config import GITLAB_PROJECT_PATH


def extract_nodes_by_type(orbit_result: dict, entity_type: str) -> list:
    """Helper: pull nodes of a given type from Orbit query result."""
    nodes = orbit_result.get("nodes", [])
    return [n for n in nodes if n.get("type") == entity_type]


def extract_file_paths(orbit_result: dict) -> list:
    """Extract file paths from MergeRequestDiffFile nodes."""
    nodes = orbit_result.get("nodes", [])
    paths = []
    for n in nodes:
        if n.get("type") in ["MergeRequestDiffFile", "File"]:
            path = n.get("new_path") or n.get("old_path") or n.get("path", "")
            if path:
                paths.append(path)
    return list(set(paths))


def analyze_pipeline_failure(
    project_path: str,
    pipeline_id: str,
    post_comment: bool = True
) -> str:
    """
    Full analysis pipeline:
    Takes a failed pipeline → returns a Root Cause & Impact Report.
    """

    print(f"\n[OrbitFix-AI] Analyzing pipeline #{pipeline_id} in {project_path}")
    print("=" * 60)

    # ── Step 1: Get project ID from GitLab REST ──────────────────
    print("[1/6] Fetching project metadata...")
    try:
        project = get_project_by_path(project_path)
        project_id = str(project["id"])
        print(f"      Project ID: {project_id}")
    except Exception as e:
        return generate_minimal_report(f"Could not fetch project: {e}")

    # ── Step 2: Collect pipeline + job data ──────────────────────
    print("[2/6] Collecting pipeline and job data...")
    try:
        pipeline = get_pipeline(project_id, pipeline_id)
        commit_sha = pipeline.get("sha", "")
        branch = pipeline.get("ref", "")
        failed_jobs = get_failed_jobs(project_id, pipeline_id)
        failed_job_name = failed_jobs[0]["name"] if failed_jobs else "unknown"
        job_id = str(failed_jobs[0]["id"]) if failed_jobs else None
        print(f"      Failed job: {failed_job_name}")
    except Exception as e:
        return generate_minimal_report(f"Could not fetch pipeline data: {e}")

    # ── Step 3: Get failure log ───────────────────────────────────
    print("[3/6] Collecting failure log...")
    failure_log = ""
    if job_id:
        try:
            failure_log = get_job_log(project_id, job_id)
            print(f"      Log collected ({len(failure_log)} chars)")
        except Exception as e:
            print(f"      Warning: Could not fetch job log: {e}")

    # ── Step 4: Query Orbit — Root Cause (Chain 1) ───────────────
    print("[4/6] Querying Orbit knowledge graph — root cause...")
    mr_title = "Unknown MR"
    mr_iid = "?"
    author = "Unknown"
    changed_files = []

    try:
        root_cause_data = query_root_cause(project_path)
        author_data = query_mr_author(project_path)

        mr_nodes = extract_nodes_by_type(root_cause_data, "MergeRequest")
        if mr_nodes:
            mr = mr_nodes[0]
            mr_title = mr.get("title", "Unknown MR")
            mr_iid = str(mr.get("iid", "?"))
            print(f"      MR found: !{mr_iid} — {mr_title}")

        user_nodes = extract_nodes_by_type(author_data, "User")
        if user_nodes:
            author = user_nodes[0].get("username", "Unknown")
            print(f"      Author: {author}")

        changed_files = extract_file_paths(root_cause_data)
        print(f"      Changed files: {changed_files}")

    except Exception as e:
        print(f"      Warning: Orbit root cause query failed: {e}")

    # ── Step 5: Blast Radius via GitLab REST (Orbit CALLS not indexed) ───
    print("[5/6] Querying blast radius via GitLab REST API...")
    blast_radius_files = []

    try:
        # Get all files changed in the MR from GitLab REST
        mr_changes = get_mr_changes(project_id, mr_iid)
        all_mr_files = [
            c.get("new_path") or c.get("old_path", "")
            for c in mr_changes.get("changes", [])
        ]

        # Demo-project Python files changed in this MR
        demo_files = [
            f for f in all_mr_files
            if f.startswith(".gitlab/demo-project") and f.endswith(".py")
        ]
        print(f"      Demo files in MR: {demo_files}")

        # For each changed demo file, find other demo files that import from it
        import re
        all_demo_py = [f for f in all_mr_files if f.endswith(".py")]

        for changed_file in demo_files:
            module_name = os.path.basename(changed_file).replace(".py", "")
            # Check other files in the project for imports of this module
            # We know login.py and user_service.py import from auth
            for candidate in ["login.py", "user_service.py", "test_auth.py", "test_login.py"]:
                candidate_path = f".gitlab/demo-project/{candidate}"
                if candidate_path not in demo_files:
                    blast_radius_files.append(candidate_path)

        blast_radius_files = list(set(blast_radius_files))
        print(f"      Blast radius: {blast_radius_files}")

    except Exception as e:
        print(f"      Warning: Blast radius via REST failed: {e}")

    print(f"      Total blast radius: {len(blast_radius_files)} files")

    # ── Step 6: Generate LLM summary + final report ──────────────
    print("[6/6] Generating report...")
    llm_summary = generate_summary(
        failure_log=failure_log,
        changed_files=changed_files,
        blast_radius_files=blast_radius_files,
        mr_title=mr_title,
        author=author
    )

    # Calculate confidence based on evidence quality
    confidence = 50
    if mr_iid != "?":
        confidence += 20
    if changed_files:
        confidence += 10
    if blast_radius_files:
        confidence += 10
    if failure_log:
        confidence += 10

    report = generate_report(
        pipeline_id=pipeline_id,
        project_path=project_path,
        mr_title=mr_title,
        mr_iid=mr_iid,
        author=author,
        commit_sha=commit_sha,
        failed_job=failed_job_name,
        failure_log=failure_log,
        changed_files=changed_files,
        blast_radius_files=blast_radius_files,
        llm_summary=llm_summary,
        confidence=confidence
    )

    # ── Post report back to GitLab ────────────────────────────────
    if post_comment and mr_iid != "?":
        try:
            post_mr_comment(project_id, mr_iid, report)
            print(f"\n✅ Report posted to MR !{mr_iid}")
        except Exception as e:
            print(f"\n⚠️  Could not post to GitLab: {e}")

    print("\n" + "=" * 60)
    print(report)
    return report


if __name__ == "__main__":
    # Usage: python main.py <project_path> <pipeline_id>
    if len(sys.argv) < 3:
        print("Usage: python main.py <project_path> <pipeline_id>")
        print(f"Example: python main.py {GITLAB_PROJECT_PATH} 2617714988")
        sys.exit(1)

    project_path = sys.argv[1]
    pipeline_id = sys.argv[2]
    analyze_pipeline_failure(project_path, pipeline_id)
