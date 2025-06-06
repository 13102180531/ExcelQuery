# app/excel/models.py

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- LLM Config Models (remain the same) ---
class LLMProviderConfig(BaseModel):
    apiKey: Optional[str] = None
    apiUrl: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None
    topP: Optional[float] = None

class LLMConfig(BaseModel):
    apiType: str
    siliconflow: Optional[LLMProviderConfig] = None
    ollama: Optional[LLMProviderConfig] = None

# --- Request Models (remain largely the same) ---
class ExcelQueryRequest(BaseModel):
    query: str
    config: Optional[LLMConfig] = None
    # file_id_to_query: Optional[int] = None # Optional: To specify which uploaded file

class ExcelDownloadRequest(BaseModel):
    query: Optional[str] = None
    parsed_conditions: Optional[Dict[str, Any]] = None
    config: Optional[LLMConfig] = None
    # file_id_to_download: Optional[int] = None # Optional

# --- CORRECTED FileUploadResponse for "save original file metadata" strategy ---
class FileUploadResponseItem(BaseModel): # Information for each successfully saved original file
    original_filename: str      # The name of the file as uploaded by the user
    stored_server_filename: str # The (potentially timestamped/unique) name used on the server
    stored_path: str            # Full path on server (primarily for backend/debug use)
    size_bytes: int             # Size of the uploaded file
    mime_type: Optional[str] = None
    db_record_id: int           # The ID of the record created in UploadedExcelFile table
    message: str                # e.g., "File saved successfully."

class FileUploadResponse(BaseModel):
    success: bool # Overall success (e.g., true if at least one file processed)
    # List of details for each file that was successfully saved and had a DB record created
    details: List[FileUploadResponseItem]
    # List of error messages for files that failed (e.g., "File X is not a valid Excel file")
    errors: List[str]


# --- Query/Download Response Models (remain the same, source_files will list original names) ---
class QueryExecutionResponse(BaseModel):
    query: str
    parsed_conditions: Dict[str, Any]
    results: List[Dict[str, Any]]
    source_files: List[str] # Original filenames of the file(s) used for this query

# For listing files associated with a group
class UploadedExcelFileResponse(BaseModel): # Pydantic model for API response when listing files
    id: int
    original_filename: str
    # stored_file_path: str # Consider if you want to expose full server paths
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    upload_timestamp: datetime
    uploader_id: int # Could be enriched with username if needed
    user_group_id: int # Could be enriched with group name

    class Config:
        from_attributes = True