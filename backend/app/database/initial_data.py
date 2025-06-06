# Example: app/initial_data.py
from sqlmodel import Session, select
from app.database.models import UserGroup
from app.users.models import UserGroupCreate # Assuming you have this Pydantic model
from app.users.crud import create_user_group, get_user_group_by_name # Your CRUD functions

def create_default_user_group(db: Session) -> None:
    default_group_name = "default"
    group = get_user_group_by_name(db, name=default_group_name)
    if not group:
        print(f"Creating default user group: '{default_group_name}'")
        default_group_schema = UserGroupCreate(
            name=default_group_name,
            description="Default user group for new users"
        )
        create_user_group(db, group=default_group_schema)
        print(f"Default user group '{default_group_name}' created successfully.")
    else:
        print(f"Default user group '{default_group_name}' already exists.")