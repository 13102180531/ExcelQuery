from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

# UserGroup Model (no change)
class UserGroup(SQLModel, table=True):
    __tablename__ = "user_groups"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    users: List["User"] = Relationship(back_populates="group")
    excel_files: List["UploadedExcelFile"] = Relationship(back_populates="group")

# User Model (no change)
class User(SQLModel, table=True):
    __tablename__ = "app_users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    user_group_id: Optional[int] = Field(default=None, foreign_key="user_groups.id", index=True)
    group: Optional[UserGroup] = Relationship(back_populates="users")
    uploaded_files: List["UploadedExcelFile"] = Relationship(back_populates="uploader")

# --- UploadedExcelFile Model (Simplified for storing original file path) ---
class UploadedExcelFile(SQLModel, table=True):
    __tablename__ = "uploaded_excel_files"
    id: Optional[int] = Field(default=None, primary_key=True)
    original_filename: str = Field(max_length=255) # Name of the file as uploaded by user
    stored_file_path: str = Field(max_length=512, unique=True) # Full path to the saved file on server
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = Field(default=None, max_length=100)
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)

    uploader_id: int = Field(foreign_key="app_users.id", index=True)
    uploader: User = Relationship(back_populates="uploaded_files")

    user_group_id: int = Field(foreign_key="user_groups.id", index=True)
    group: UserGroup = Relationship(back_populates="excel_files")