import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY environment variable is not set")

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def verify_api_key(x_api_key: str | None = Security(api_key_header)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Clé API invalide")
