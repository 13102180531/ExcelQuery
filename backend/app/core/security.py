from datetime import datetime, timedelta, timezone # Added timezone for JWT
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import Session # For type hinting db session if needed by a function here

from app.core.config import settings
# Corrected import for get_db
from app.database.setup import get_db # <<<<< CORRECTED IMPORT HERE
from app.database.models import User # User model is fine here for type hinting if needed

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Note: get_current_active_user and get_current_user_from_token
# are now in app.core.dependencies.py to avoid circular imports with routers.
# If security.py needed to decode a token and fetch a user directly (without being a FastAPI dependency),
# it would look something like this, but it would need access to a db session.

# Example (if this file needed to do standalone user fetching from token, which it currently doesn't):
# def get_user_from_token_payload(db: Session, payload: dict) -> Optional[User]:
#     from app.users.crud import get_user_by_username # Local import to avoid circularity if called rarely
#     username: str = payload.get("sub")
#     if username is None:
#         return None
#     user = get_user_by_username(db, username=username)
#     return user