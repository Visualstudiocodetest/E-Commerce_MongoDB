"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load the .env located at the project root (one level above /backend)
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ecommerce")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production-use-a-real-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
