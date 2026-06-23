import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITLAB_TOKEN")
url = "https://gitlab.com/api/v4/orbit/query"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

query = {
    "query": {
        "query_type": "traversal",
        "nodes": [
            {
                "id": "p",
                "entity": "Project",
                "filters": {"full_path": {"op": "contains", "value": "orbitfix-ai-dev"}}
            },
            {"id": "f", "entity": "File"},
            {"id": "d", "entity": "Definition"}
        ],
        "relationships": [
            {"type": "IN_PROJECT", "from": "f", "to": "p"},
            {"type": "DEFINES", "from": "f", "to": "d"}
        ],
        "limit": 50
    },
    "format": "raw"
}

r = requests.post(url, headers=headers, json=query)
data = r.json()
result = data.get("result", data)
nodes = result.get("nodes", [])

print(f"Total nodes returned: {len(nodes)}")
print()
for n in nodes:
    node_type = n.get("type", "unknown")
    name = n.get("name") or n.get("path") or n.get("title") or str(n)[:80]
    print(f"  [{node_type}] {name}")