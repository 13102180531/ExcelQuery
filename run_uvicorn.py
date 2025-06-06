import uvicorn
from backend.app.main import app # Assuming your FastAPI app instance is in app/main.py

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) # reload=True for development