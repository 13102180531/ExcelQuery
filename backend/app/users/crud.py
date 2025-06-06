from sqlmodel import Session, select
from app.database.models import User, UserGroup  # Import UserGroup
from app.users.models import UserCreate, UserGroupCreate  # User domain Pydantic model
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
from typing import List, Optional  # <<<<< ADDED IMPORT FOR List and Optional


# --- UserGroup CRUD Functions (New) ---
def get_user_group_by_name(db: Session, name: str) -> UserGroup | None:
    statement = select(UserGroup).where(UserGroup.name == name)
    return db.exec(statement).first()


def get_user_group_by_id(db: Session, group_id: int) -> UserGroup | None:
    return db.get(UserGroup, group_id)


def create_user_group(db: Session, group: UserGroupCreate) -> UserGroup:
    # SQLModel v0.0.14+ uses model_validate
    # For older versions, it might be UserGroup.from_orm(group) or UserGroup(**group.dict())
    try:
        db_group = UserGroup.model_validate(group)
    except AttributeError:  # Fallback for older SQLModel/Pydantic
        db_group = UserGroup(**group.model_dump())  # Use model_dump for Pydantic v2
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


def get_all_user_groups(db: Session, skip: int = 0, limit: int = 100) -> List[UserGroup]:  # Now List is defined
    statement = select(UserGroup).offset(skip).limit(limit)
    return db.exec(statement).all()


# --- User CRUD Functions (Modified create_user, authenticate_user) ---
def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    return db.exec(statement).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    group = get_user_group_by_name(db, name="default")
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User group '{user_in.user_group_name}' not found. Please create it first or choose an existing one."
        )
    # else: user can be created without a group, or assign a default group if desired
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        user_group_id=group.id,  # Assign the group ID
        is_active=True,  # Default to active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    user = get_user_by_username(db, username=identifier)
    if not user:
        user = get_user_by_email(db, email=identifier)
    if not user:
        return None
    if not user.is_active:  # Check if user is active
        return None  # Or raise specific exception for inactive user
    if not verify_password(password, user.hashed_password):
        return None
    return user  # User object now contains user_group_id


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    """ Fetches a user by username or email. """
    user = db.exec(select(User).where(User.username == identifier)).first()
    if not user:
        user = db.exec(select(User).where(User.email == identifier)).first()
    return user
