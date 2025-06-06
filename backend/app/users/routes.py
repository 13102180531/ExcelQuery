from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import timedelta
from typing import List

from app.users import crud as user_crud, models as user_models
from app.database.setup import get_db
from app.database.models import User as DBUser, UserGroup as DBUserGroup # Import UserGroup
from app.core import security
from app.core.config import settings
from app.core.dependencies import get_current_active_user

router = APIRouter()

# --- UserGroup Routes (New) ---
@router.post("/groups", response_model=user_models.UserGroupResponse, status_code=status.HTTP_201_CREATED)
def create_new_user_group(
    group_in: user_models.UserGroupCreate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user) # Optional: Protect group creation
):
    # Add admin check here if only admins can create groups
    # if current_user.user_group_id != ADMIN_GROUP_ID: # Pseudo-code
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create groups")
    existing_group = user_crud.get_user_group_by_name(db, name=group_in.name)
    if existing_group:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group name already exists")
    return user_crud.create_user_group(db, group=group_in)

@router.get("/groups", response_model=List[user_models.UserGroupResponse])
def read_all_user_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return user_crud.get_all_user_groups(db, skip=skip, limit=limit)

@router.get("/groups/{group_id}", response_model=user_models.UserGroupResponse)
def read_user_group(group_id: int, db: Session = Depends(get_db)):
    group = user_crud.get_user_group_by_id(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group

# --- User Routes (Modified login and register) ---
@router.post("/register", response_model=user_models.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user_route(user_in: user_models.UserCreate, db: Session = Depends(get_db)):
    # ... (existing username/email checks) ...
    db_user_by_username = user_crud.get_user_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    db_user_by_email = user_crud.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    # The create_user crud now handles user_group_name
    user = user_crud.create_user(db=db, user_in=user_in)
    return user

@router.post("/login", response_model=user_models.Token)
def login_for_access_token_route(
    form_data: user_models.UserLogin,
    db: Session = Depends(get_db)
):
    user = user_crud.authenticate_user(db, identifier=form_data.identifier, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password, or inactive account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user.username,
        "user_id": user.id,
    }
    if user.user_group_id: # Add group ID to token if user belongs to a group
        token_data["user_group_id"] = user.user_group_id

    access_token = security.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=user_models.UserResponse)
async def read_users_me_route(current_user: DBUser = Depends(get_current_active_user)):
    # The current_user object (DBUser) now includes the 'group' relationship,
    # which will be serialized by UserResponse Pydantic model.
    return current_user