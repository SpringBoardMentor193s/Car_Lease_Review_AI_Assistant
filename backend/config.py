import os

# Toggle LLM usage (mentor-safe switch)
USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# Placeholder for future LLM key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
