import os
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
import jwt
from backend.models import User

import secrets
import sys

_raw_secret = os.getenv("SECRET_KEY", "")

# Fail fast if the secret is missing or still the old insecure default.
_INSECURE_DEFAULTS = {"", "supersecretkey_change_in_production", "changeme"}
if _raw_secret in _INSECURE_DEFAULTS:
    if os.getenv("ALLOW_INSECURE_SECRET") == "1":
        # Dev-only escape hatch — must be explicitly opted in.
        import warnings
        _raw_secret = secrets.token_hex(32)
        warnings.warn(
            "SECRET_KEY not set — using a random key. "
            "All tokens will be invalidated on restart. "
            "Set SECRET_KEY in production.",
            stacklevel=1,
        )
    else:
        print(
            "FATAL: SECRET_KEY environment variable is not set or is insecure.\n"
            "Set a strong SECRET_KEY before starting the server.\n"
            "For local dev only, set ALLOW_INSECURE_SECRET=1 to bypass.",
            file=sys.stderr,
        )
        sys.exit(1)

SECRET_KEY = _raw_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
