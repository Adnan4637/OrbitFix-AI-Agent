import sys
import os
import subprocess
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import GITLAB_GROUP, ORBIT_QUERY_LIMIT



def run_orbit_query(query: dict) -> dict:
    """Send a query to Orbit Remote via glab CLI and return parsed JSON result."""
    query_json = json.dumps(query)
    result = subprocess.run(
        ["glab", "orbit", "remote", "query", "-", "--format", "raw"],
        input=query_json,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Orbit query failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # glab may return LLM-format text — fall back gracefully
        return {"raw": result.stdout, "nodes": [], "edges": []}


def query_project(project_path: str) -> dict:
    """Confirm project is indexed in Orbit."""
    query = {
        "query": {
            "query_type": "traversal",
            "node": {
                "id": "p",
                "entity": "Project",
                "filters": {
                    "full_path": {"op": "contains", "value": project_path}
                }
            },
            "limit": 1
        }
    }
    return run_orbit_query(query)


def query_root_cause(project_path: str) -> dict:
    """
    Chain 1: MR → Author → Changed files for a project.
    Finds the most recent MR, who wrote it, and what files it changed.
    This is the core root-cause traversal.
    """
    query = {
        "query": {
            "query_type": "traversal",
            "nodes": [
                {
                    "id": "p",
                    "entity": "Project",
                    "filters": {
                        "full_path": {"op": "contains", "value": project_path}
                    }
                },
                {"id": "mr", "entity": "MergeRequest"},
                {"id": "diff", "entity": "MergeRequestDiff"},
                {"id": "file", "entity": "MergeRequestDiffFile"}
            ],
            "relationships": [
                {"type": "IN_PROJECT", "from": "mr", "to": "p"},
                {"type": "HAS_LATEST_DIFF", "from": "mr", "to": "diff"},
                {"type": "HAS_FILE", "from": "diff", "to": "file"}
            ],
            "limit": ORBIT_QUERY_LIMIT
        }
    }
    return run_orbit_query(query)


def query_mr_author(project_path: str) -> dict:
    """
    Get who authored each MR in the project.
    Uses AUTHORED edge: User → MergeRequest.
    """
    query = {
        "query": {
            "query_type": "traversal",
            "nodes": [
                {
                    "id": "p",
                    "entity": "Project",
                    "filters": {
                        "full_path": {"op": "contains", "value": project_path}
                    }
                },
                {"id": "mr", "entity": "MergeRequest"},
                {"id": "u", "entity": "User"}
            ],
            "relationships": [
                {"type": "IN_PROJECT", "from": "mr", "to": "p"},
                {"type": "AUTHORED", "from": "u", "to": "mr"}
            ],
            "limit": ORBIT_QUERY_LIMIT
        }
    }
    return run_orbit_query(query)


def query_blast_radius(project_path: str, file_path: str) -> dict:
    """
    Chain 2: Given a changed file, find all dependent files.
    File → Definitions → Callers (reverse CALLS) → Their Files.
    This is the blast-radius / impact analysis traversal.
    """
    query = {
        "query": {
            "query_type": "traversal",
            "nodes": [
                {
                    "id": "p",
                    "entity": "Project",
                    "filters": {
                        "full_path": {"op": "contains", "value": project_path}
                    }
                },
                {
                    "id": "f",
                    "entity": "File",
                    "filters": {
                        "path": {"op": "contains", "value": file_path}
                    }
                },
                {"id": "def", "entity": "Definition"},
                {"id": "caller", "entity": "Definition"},
                {"id": "caller_file", "entity": "File"}
            ],
            "relationships": [
                {"type": "IN_PROJECT", "from": "f", "to": "p"},
                {"type": "DEFINES", "from": "f", "to": "def"},
                {"type": "CALLS", "from": "caller", "to": "def"},
                {"type": "DEFINES", "from": "caller_file", "to": "caller"}
            ],
            "limit": ORBIT_QUERY_LIMIT
        }
    }
    return run_orbit_query(query)


def query_all_files(project_path: str) -> dict:
    """List all source files indexed in the project."""
    query = {
        "query": {
            "query_type": "traversal",
            "nodes": [
                {
                    "id": "p",
                    "entity": "Project",
                    "filters": {
                        "full_path": {"op": "contains", "value": project_path}
                    }
                },
                {"id": "f", "entity": "File"}
            ],
            "relationships": [
                {"type": "IN_PROJECT", "from": "f", "to": "p"}
            ],
            "limit": ORBIT_QUERY_LIMIT
        }
    }
    return run_orbit_query(query)


def query_imports(project_path: str, file_path: str) -> dict:
    """
    Find what symbols a file imports.
    File → ImportedSymbol (one-hop, simpler alternative to full blast-radius).
    """
    query = {
        "query": {
            "query_type": "traversal",
            "nodes": [
                {
                    "id": "p",
                    "entity": "Project",
                    "filters": {
                        "full_path": {"op": "contains", "value": project_path}
                    }
                },
                {
                    "id": "f",
                    "entity": "File",
                    "filters": {
                        "path": {"op": "contains", "value": file_path}
                    }
                },
                {"id": "sym", "entity": "ImportedSymbol"}
            ],
            "relationships": [
                {"type": "IN_PROJECT", "from": "f", "to": "p"},
                {"type": "IMPORTS", "from": "f", "to": "sym"}
            ],
            "limit": ORBIT_QUERY_LIMIT
        }
    }
    return run_orbit_query(query)
