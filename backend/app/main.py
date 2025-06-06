from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import domain-specific routers
from app.users import routes as user_api_router
from app.excel import routes as excel_api_router

# Import database setup
from app.database.setup import create_db_and_tables, engine
from app.database.initial_data import create_default_user_group
from sqlmodel import SQLModel, Session
# Create database tables on startup
create_db_and_tables()

app = FastAPI(
    title="Modular Excel Query Tool API",
    version="0.3.0",
    description="API with domain-based structure for user auth and Excel querying.",
    # openapi_url="/api/v1/openapi.json" # If you want to customize OpenAPI path
)

# CORS Middleware
origins = [
    "*", # For development. Be more specific for production.
    # "http://localhost:5173",
    # "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Optional: Create database tables if they don't exist
    # This is often done once, or managed by Alembic migrations in production
    # SQLModel.metadata.create_all(engine)
    # print("Database tables checked/created.")

    # Create a temporary session to add initial data
    # It's important that tables exist before trying to add data
    with Session(engine) as session:
        try:
            create_default_user_group(session)
            # You can add other initial data here if needed
            session.commit() # Commit if create_default_user_group doesn't commit itself
                           # (Your current create_user_group commits)
        except Exception as e:
            print(f"Error during startup data initialization: {e}")
            session.rollback()

# Include domain-specific routers
app.include_router(user_api_router.router, prefix="/api/v1/users", tags=["User Management & Authentication"])
app.include_router(excel_api_router.router, prefix="/api/v1/excel", tags=["Excel Data Processing"])

# Global health check
@app.get("/api/v1/health", tags=["System Health"])
def health_check():
    return {"status": "healthy", "message": "API is operational."}

# To run with uvicorn from the project root: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    # Make sure to run from the project root directory (your_project_root)
    # so that 'app.main:app' resolves correctly.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)