from pydantic import BaseModel, EmailStr, field_validator, constr
from datetime import datetime
from typing import Optional

# --- UserGroup Pydantic Models (New) ---
class UserGroupBase(BaseModel):
    name: constr(min_length=2, max_length=100)
    description: Optional[str] = None

class UserGroupCreate(UserGroupBase):
    pass

class UserGroupResponse(UserGroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- User Pydantic Models (Updated) ---
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=6, max_length=128)
    confirm_password: str
    user_group_name: Optional[str] = None

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    is_active: bool
    group: Optional[UserGroupResponse] = None # Show group info

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    user_group_id: Optional[int] = None # Add group_id to token for easier access

class UserLogin(BaseModel):
    identifier: str
    password: str