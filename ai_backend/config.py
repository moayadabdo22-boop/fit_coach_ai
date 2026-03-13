import os
import logging
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
# Default to free local AI (Ollama). Use LLM_PROVIDER=openai only when explicitly needed.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

# Supabase Configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY", "")

# FAISS Configuration
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./ai_backend/faiss_index")
EXERCISES_DATA_PATH = os.getenv("EXERCISES_DATA_PATH", "./ai_backend/exercises.json")

# API Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./ai_backend/logs/app.log")

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Memory Configuration
SHORT_TERM_MEMORY_SIZE = int(os.getenv("SHORT_TERM_MEMORY_SIZE", "10"))
LONG_TERM_MEMORY_ENABLED = os.getenv("LONG_TERM_MEMORY_ENABLED", "true").lower() == "true"

# Streaming Configuration
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
STREAMING_CHUNK_SIZE = int(os.getenv("STREAMING_CHUNK_SIZE", "50"))

# Setup Logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
