from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session

from app.database.setup import get_db
from app.database.models import User
from app.users import crud as user_crud
from app.users import models as user_models # For TokenData
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_group_id: Optional[int] = payload.get("user_group_id") # Get group_id

        if username is None or user_id is None: # group_id can be None if user not in group
            raise credentials_exception

        # Store in a Pydantic model for clarity, though not strictly needed here if just fetching user
        # token_data = user_models.TokenData(username=username, user_id=user_id, user_group_id=user_group_id)

    except JWTError:
        raise credentials_exception

    user = user_crud.get_user_by_id(db, user_id=user_id) # Fetch by ID for security
    if user is None:
        raise credentials_exception
    if user.username != username: # Sanity check
        raise credentials_exception
    # user.user_group_id will be available on the fetched user object
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user_from_token)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user