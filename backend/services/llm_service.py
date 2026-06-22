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
    prompt = f"""You are an expert software engineer analyzing a CI pipeline failure.

Evidence from GitLab Orbit knowledge graph:
- Failed job log: {failure_log[:2000]}
- Merge Request: {mr_title}
- Author: {author}
- Files changed in MR: {", ".join(changed_files) if changed_files else "unknown"}
- Files in blast radius: {", ".join(blast_radius_files) if blast_radius_files else "none detected"}

Write a concise 3-5 sentence root cause summary. Be specific. Reference file names."""

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
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