# gitlab_client.py
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests

from config import GITLAB_TOKEN, GITLAB_URL

HEADERS = {
    "PRIVATE-TOKEN": GITLAB_TOKEN,
    "Content-Type": "application/json"
}
def _get(url: str, params: dict = None) -> dict | list:
    """Generic GET request to GitLab REST API."""
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()
def _post(url: str, data: dict) -> dict:
    """Generic POST request to GitLab REST API."""
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    return response.json()


def get_pipeline(project_id: str, pipeline_id: str) -> dict:
    """Get pipeline metadata."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
    return _get(url)


def get_pipeline_jobs(project_id: str, pipeline_id: str) -> list:
    """Get all jobs in a pipeline."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    return _get(url)


def get_failed_jobs(project_id: str, pipeline_id: str) -> list:
    """Get only the failed jobs in a pipeline."""
    jobs = get_pipeline_jobs(project_id, pipeline_id)
    return [j for j in jobs if j.get("status") == "failed"]


def get_job_log(project_id: str, job_id: str) -> str:
    """Get the raw log/trace for a job (last 5000 chars to avoid huge logs)."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/jobs/{job_id}/trace"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    log = response.text
    # Return last 5000 chars — the failure message is almost always at the end
    return log[-5000:] if len(log) > 5000 else log


def get_recent_commits(project_id: str, branch: str = None, limit: int = 10) -> list:
    """Get recent commits on a branch."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits"
    params = {"per_page": limit}
    if branch:
        params["ref_name"] = branch
    return _get(url, params)


def get_recent_mrs(project_id: str, limit: int = 5) -> list:
    """Get recently merged MRs."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests"
    params = {
        "state": "merged",
        "order_by": "updated_at",
        "sort": "desc",
        "per_page": limit
    }
    return _get(url, params)


def get_mr_changes(project_id: str, mr_iid: str) -> dict:
    """Get changed files for a specific MR."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
    return _get(url)


def get_project_by_path(project_path: str) -> dict:
    """Get project details by full path (URL-encoded)."""
    encoded = project_path.replace("/", "%2F")
    url = f"{GITLAB_URL}/api/v4/projects/{encoded}"
    return _get(url)


def post_mr_comment(project_id: str, mr_iid: str, comment: str) -> dict:
    """Post a comment (note) on a merge request."""
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
    return _post(url, {"body": comment})


def post_pipeline_comment(project_id: str, pipeline_id: str, comment: str) -> dict:
    """Post a comment on the commit that triggered the pipeline."""
    pipeline = get_pipeline(project_id, pipeline_id)
    sha = pipeline.get("sha", "")
    url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits/{sha}/comments"
    return _post(url, {"note": comment})
