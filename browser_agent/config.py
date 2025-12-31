import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Compatible Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio") # LM Studio doesn't strictly need a real key usually
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "local-model") # default to a generic name, user can override

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
