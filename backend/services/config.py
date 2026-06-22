import os
from dotenv import load_dotenv

load_dotenv()

# GitLab Configuration
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_GROUP = os.getenv("GITLAB_GROUP", "m.adnan4637-group")
GITLAB_PROJECT_PATH = os.getenv("GITLAB_PROJECT_PATH", "m.adnan4637-group/orbitfix-ai-dev")

# LLM Configuration
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
LLM_API_URL = os.getenv("LLM_API_URL", "https://api.anthropic.com/v1/messages")

# Orbit Configuration
ORBIT_QUERY_LIMIT = int(os.getenv("ORBIT_QUERY_LIMIT", "20"))
