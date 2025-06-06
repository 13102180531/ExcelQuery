from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    # Import all models that need to be created BEFORE calling create_all
    from app.database.models import User, UserGroup, UploadedExcelFile # ADDED UserGroup, UploadedExcelFile
    print("Attempting to create database tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully (or already exist).")
    except Exception as e:
        print(f"!!!!!!!! ERROR DURING create_db_and_tables !!!!!!!!")
        import traceback
        traceback.print_exc()
        print(f"Error details: {e}")

def get_db():
    with Session(engine) as session:
        yield session