import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from config import LLM_API_KEY, LLM_MODEL, LLM_API_URL


def generate_summary(
    failure_log: str,
    changed_files: list,
    blast_radius_files: list,
    mr_title: str,
    author: str
) -> str:
    # Extract only the relevant error lines from the log
    error_lines = [
        line for line in failure_log.splitlines()
        if any(kw in line for kw in ["Error", "ERROR", "ImportError", "Exception", "FAILED", "assert"])
    ]
    relevant_log = "\n".join(error_lines[:20]) if error_lines else failure_log[-500:]

    prompt = f"""You are an expert software engineer analyzing a CI pipeline failure.

Evidence from GitLab Orbit knowledge graph:
- Key error lines from job log:
{relevant_log}
- Merge Request: {mr_title}
- Author: {author}
- Files changed in MR: {", ".join(changed_files) if changed_files else "unknown"}
- Files in blast radius: {", ".join(blast_radius_files) if blast_radius_files else "none detected"}

Write a concise 3-5 sentence root cause summary focusing on the actual error. Reference file names and the MR."""

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.3
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"LLM summary unavailable: {str(e)}"