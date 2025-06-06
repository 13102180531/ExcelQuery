# app/excel/temp_store.py
import logging
import uuid
import time
import shutil
from typing import Dict, Any, Optional
import pandas as pd
import threading
from pathlib import Path
from app.core.config import settings # For base directory configuration

# --- Configuration ---
# Use a dedicated directory for temporary query results
TEMP_RESULTS_DIR_NAME = "temp_query_results"
# Ensure base path is configurable, default to a 'data' subdirectory
BASE_DATA_DIR = Path(settings.APP_DATA_DIR if hasattr(settings, 'APP_DATA_DIR') else "./data")
TEMP_RESULTS_DIR = BASE_DATA_DIR / TEMP_RESULTS_DIR_NAME
TEMP_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_METADATA_TTL_SECONDS = 60 * 60  # 1 hour for metadata and temp file lifetime

# Metadata structure: {result_id: {"filepath": Path, "timestamp": float, "query_params": dict}}
_results_metadata_store: Dict[str, Dict[str, Any]] = {}
_metadata_lock = threading.Lock()

logger = logging.getLogger(__name__) # Assuming logger is configured in calling modules or here

def generate_result_id() -> str:
    return str(uuid.uuid4())

def store_query_result_as_file(query_params: Dict[str, Any], results_df: pd.DataFrame) -> Optional[str]:
    result_id = generate_result_id()
    # Sanitize query or use part of original filename for a slightly more readable temp filename
    # For simplicity, just use result_id for the filename.
    temp_filename = f"{result_id}.parquet"
    temp_filepath = TEMP_RESULTS_DIR / temp_filename

    try:
        results_df.to_parquet(temp_filepath, index=False)
        with _metadata_lock:
            _results_metadata_store[result_id] = {
                "filepath": temp_filepath,
                "timestamp": time.time(),
                "query_params": query_params
            }
        logger.info(f"Stored query result {result_id} to {temp_filepath}")
        return result_id
    except Exception as e:
        logger.error(f"Failed to store query result {result_id} to file {temp_filepath}: {e}", exc_info=True)
        # Attempt to clean up partial file if it exists
        if temp_filepath.exists():
            try:
                temp_filepath.unlink()
            except OSError:
                logger.error(f"Could not remove partial temp file {temp_filepath}", exc_info=True)
        return None


def get_query_result_from_file(result_id: str) -> Optional[pd.DataFrame]:
    metadata = None
    with _metadata_lock:
        metadata = _results_metadata_store.get(result_id)

    if not metadata:
        logger.warning(f"No metadata found for result_id: {result_id}")
        return None

    if (time.time() - metadata["timestamp"]) >= RESULTS_METADATA_TTL_SECONDS:
        logger.info(f"Result {result_id} has expired. Cleaning up.")
        cleanup_single_result(result_id) # Cleans up metadata and file
        return None

    try:
        df = pd.read_parquet(metadata["filepath"])
        logger.info(f"Retrieved query result {result_id} from {metadata['filepath']}")
        return df
    except Exception as e:
        logger.error(f"Failed to read query result {result_id} from file {metadata['filepath']}: {e}", exc_info=True)
        # If file is corrupted or missing but metadata exists, consider cleaning up metadata
        # cleanup_single_result(result_id) # Potentially aggressive
        return None


def get_query_params_for_result(result_id: str) -> Optional[Dict[str, Any]]:
    with _metadata_lock:
        metadata = _results_metadata_store.get(result_id)
        if metadata:
            if (time.time() - metadata["timestamp"]) < RESULTS_METADATA_TTL_SECONDS:
                return metadata["query_params"]
            else:
                # Expired, remove it (metadata only, file cleanup handled by get_query_result or periodic cleanup)
                # Actually, better to have cleanup_single_result handle both
                cleanup_single_result(result_id)
                return None
        return None

def cleanup_single_result(result_id: str):
    """Removes metadata and the associated temporary file."""
    with _metadata_lock:
        metadata = _results_metadata_store.pop(result_id, None)

    if metadata and metadata.get("filepath"):
        filepath_to_delete = Path(metadata["filepath"])
        if filepath_to_delete.exists():
            try:
                filepath_to_delete.unlink()
                logger.info(f"Cleaned up temporary result file: {filepath_to_delete}")
            except OSError as e:
                logger.error(f"Error deleting temporary result file {filepath_to_delete}: {e}", exc_info=True)
        else:
            logger.warning(f"Temporary result file for {result_id} not found at {filepath_to_delete} during cleanup.")


def periodic_cleanup_expired_results():
    """Call this periodically to clean up all expired results."""
    with _metadata_lock:
        now = time.time()
        expired_ids = [
            rid for rid, meta in _results_metadata_store.items()
            if (now - meta["timestamp"]) >= RESULTS_METADATA_TTL_SECONDS
        ]

    if expired_ids:
        logger.info(f"Periodic cleanup: Found {len(expired_ids)} expired results.")
        for result_id in expired_ids:
            cleanup_single_result(result_id) # This will re-acquire lock for each, could be optimized
    else:
        logger.debug("Periodic cleanup: No expired results found.")
