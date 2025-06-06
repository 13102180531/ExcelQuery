import pandas as pd
import numpy as np
import re
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from fastapi import HTTPException, status, UploadFile
from io import BytesIO
from pathlib import Path
import uuid # For unique session names
from datetime import datetime
from sqlmodel import Session
import pyarrow
from app.core.config import settings # If you have LLM API keys here
# Assuming User and UploadedExcelFile DB models are imported where needed (e.g., from app.database.models)
from app.database.models import User as DBUser, UploadedExcelFile as DBUploadedExcelFile


logger = logging.getLogger(__name__)

# Define a directory for processed files.
# In a real app, this should come from settings.PROCESSED_FILES_DIR
UPLOADED_ORIGINAL_FILES_DIR = Path(settings.UPLOADED_ORIGINAL_FILES_DIR if hasattr(settings, 'UPLOADED_ORIGINAL_FILES_DIR') else "data/uploaded_original_files")
UPLOADED_ORIGINAL_FILES_DIR.mkdir(parents=True, exist_ok=True)


# --- Default LLM API Configuration (can be overridden by request) ---
# This could also come from settings or a dedicated config file
DEFAULT_LLM_CONFIG = {
    "apiType": "siliconflow",
    "siliconflow": {
        "apiKey": settings.SILICONFLOW_API_KEY if hasattr(settings, 'SILICONFLOW_API_KEY') else "YOUR_SILICONFLOW_KEY",
        "apiUrl": "https://api.siliconflow.cn/v1/chat/completions",
        "model": "Qwen/Qwen3-8B",
        "temperature": 0.2,
        "maxTokens": 1500
    },
    "ollama": {
        "apiUrl": "http://localhost:11434/api/chat",
        "model": "llama3",
        "temperature": 0.2,
        "topP": 0.9
    }
}
# Ensure you add SILICONFLOW_API_KEY to your .env and config.py if using it

def normalize_column_name(col_name: Any) -> str:
    if not isinstance(col_name, str):
        col_name = str(col_name)
    col_name = col_name.lower()
    col_name = re.sub(r'\s+', '_', col_name)
    col_name = re.sub(r'[^\w\u4e00-\u9fff]', '', col_name, flags=re.UNICODE) # Allow CJK characters
    col_name = re.sub(r'_+', '_', col_name)
    col_name = col_name.strip('_')
    return col_name

def generate_columns_info(df: pd.DataFrame) -> Dict:
    columns_info = {}
    if df is None or df.empty:
        return columns_info
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique_count = df[col].nunique()
        # Ensure sample_values are JSON serializable (strings)
        sample_values = df[col].dropna().sample(min(5, len(df[col].dropna()))).astype(str).tolist()
        columns_info[col] = {
            'dtype': dtype,
            'unique_count': int(unique_count),
            'sample_values': sample_values
        }
    return columns_info

async def save_original_files_and_create_records(
    db: Session, files: List[UploadFile], uploader: DBUser
) -> Tuple[List[DBUploadedExcelFile], List[str]]:
    """
    Saves each uploaded file individually and creates a database record for each.
    Returns a list of successfully created DB records and a list of errors.
    """
    created_db_records: List[DBUploadedExcelFile] = []
    processing_errors: List[str] = []
    allowed_extensions = ('.xls', '.xlsx', '.csv')

    for file_upload in files:
        original_filename = file_upload.filename
        if not original_filename:
            processing_errors.append("Received a file with no filename.")
            continue

        if not original_filename.lower().endswith(allowed_extensions):
            msg = f"Skipping '{original_filename}': Unsupported file type. Allowed: {', '.join(allowed_extensions)}."
            logger.warning(msg)
            processing_errors.append(msg)
            continue

        # Generate a unique stored filename to prevent overwrites and handle special characters
        file_timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        unique_suffix = uuid.uuid4().hex[:8]
        base, ext = Path(original_filename).stem, Path(original_filename).suffix
        # Sanitize base name (optional, but good practice)
        sanitized_base = re.sub(r'[^\w_.-]', '_', base)
        stored_server_filename = f"{sanitized_base}_{file_timestamp}_{unique_suffix}{ext}"

        stored_file_path = UPLOADED_ORIGINAL_FILES_DIR / stored_server_filename
        file_size_bytes: Optional[int] = None
        mime_type: Optional[str] = file_upload.content_type

        try:
            # Save the file to disk
            content = await file_upload.read() # Read content first to get size if not available
            file_size_bytes = len(content)

            with open(stored_file_path, "wb") as buffer:
                buffer.write(content)

            logger.info(f"Successfully saved original file '{original_filename}' to '{stored_file_path}'.")

            # Create DB record for this specific file
            db_file_record = DBUploadedExcelFile(
                original_filename=original_filename,
                stored_file_path=str(stored_file_path.resolve()),
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                uploader_id=uploader.id,
                user_group_id=uploader.user_group_id,
                upload_timestamp=datetime.utcnow() # Or use a common timestamp for the batch
            )

            db.add(db_file_record)
            created_db_records.append(db_file_record) # Add to list before commit

        except Exception as e:
            logger.error(f"Error processing and saving file '{original_filename}': {e}", exc_info=True)
            processing_errors.append(f"Error saving file '{original_filename}': {str(e)}")
            # If saving to disk failed before DB add, stored_file_path might not exist or be partial
            # If DB add fails later, it will be rolled back.
            if stored_file_path.exists():
                try:
                    stored_file_path.unlink() # Attempt to clean up partially saved file
                except OSError as ose:
                    logger.error(f"Could not delete partially saved file {stored_file_path}: {ose}")
        finally:
            await file_upload.close()

    if created_db_records: # Only commit if there are records to add
        try:
            db.commit()
            for record in created_db_records:
                db.refresh(record) # Refresh each object to get its ID etc.
            logger.info(f"Successfully committed {len(created_db_records)} file records to the database.")
        except Exception as e:
            logger.error(f"Database error committing file records: {e}", exc_info=True)
            db.rollback()
            # Critical: if commit fails, the files are on disk but records are not in DB.
            # Need a strategy for this: either delete files or log for manual cleanup.
            for record_data in created_db_records: # 'record_data' here is the uncommitted DBUploadedExcelFile instance
                failed_path = Path(record_data.stored_file_path)
                if failed_path.exists():
                    try:
                        failed_path.unlink()
                        logger.info(f"Cleaned up orphaned file due to DB commit failure: {failed_path}")
                    except OSError as ose:
                        logger.error(f"Could not delete orphaned file {failed_path} after DB commit failure: {ose}")

            processing_errors.append(f"Server error: Could not save file metadata to database. ({e})")
            created_db_records = [] # Empty the list as records were not saved

    return created_db_records, processing_errors


def read_and_prepare_dataframe_from_file(file_path_str: str) -> pd.DataFrame:
    """Reads a DataFrame from a given path (original Excel/CSV)."""
    file_path = Path(file_path_str)

    if not file_path.exists():
        logger.error(f"Data file not found at path: {file_path_str}")
        raise FileNotFoundError(f"Data file not found: {file_path_str}")

    try:
        logger.info(f"Attempting to read file: {file_path_str} with suffix: {file_path.suffix}")
        if file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path, engine=None)
        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            logger.error(f"Unsupported file type for direct read: {file_path_str}")
            raise ValueError(f"Unsupported file type for data: {file_path.suffix}")

        # Normalize column names for consistency if you plan to use generate_columns_info
        df.columns = [normalize_column_name(col) for col in df.columns]

        logger.info(f"Successfully read dataframe from {file_path_str}, shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error reading or preparing dataframe from {file_path_str}: {e}", exc_info=True)
        raise ValueError(f"Could not read or prepare data from file '{file_path.name}': {str(e)}")


def get_excel_files_for_group(db: Session, group_id: int, limit: Optional[int] = None) -> List[DBUploadedExcelFile]:
    # This function remains largely the same, but now returns individual file records
    query = db.query(DBUploadedExcelFile).filter(DBUploadedExcelFile.user_group_id == group_id).order_by(DBUploadedExcelFile.upload_timestamp.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

# --- LLM Parsing Functions (parse_with_siliconflow, parse_with_ollama) ---
# These are almost identical to your Flask app's versions.
# Make sure to handle API keys securely, e.g., from settings.

def parse_with_siliconflow(query: str, columns_info_dict: Dict, config: Dict) -> Dict:
    logger.info(f"开始使用硅基流动API解析自然语言查询: {query}")
    api_key = config.get('apiKey', DEFAULT_LLM_CONFIG['siliconflow']['apiKey'])
    api_url = config.get('apiUrl', DEFAULT_LLM_CONFIG['siliconflow']['apiUrl'])
    model = config.get('model', DEFAULT_LLM_CONFIG['siliconflow']['model'])
    temperature = float(config.get('temperature', DEFAULT_LLM_CONFIG['siliconflow']['temperature']))
    max_tokens = int(config.get('maxTokens', DEFAULT_LLM_CONFIG['siliconflow']['maxTokens']))

    if not api_key or api_key == "YOUR_SILICONFLOW_KEY": # Basic check
        logger.error("硅基流动API密钥未配置或无效。")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="硅基流动API密钥未配置。")

    system_prompt = f"""你是一个专业的数据分析助手。
你的任务是将用户的自然语言查询转换为一个结构化的JSON筛选条件对象。
这个JSON对象应该包含一个 "filters" 列表和一个可选的 "logical_operator" ("AND" 或 "OR", 默认为 "AND")。
"filters" 列表中的每个对象代表一个筛选条件，包含:
- "column": 必须是用户数据中实际存在的列名之一。
- "operator": 筛选操作符，可以是:
    - "equals": 等于 (用于精确匹配文本或数字)
    - "not_equals": 不等于
    - "contains": 包含 (用于文本部分匹配，大小写不敏感)
    - "not_contains": 不包含
    - "greater_than": 大于 (用于数字或日期)
    - "less_than": 小于 (用于数字或日期)
    - "greater_than_or_equal_to": 大于等于
    - "less_than_or_equal_to": 小于等于
    - "between": 介于两者之间 (value应为包含两个元素的列表 [min, max])
    - "not_between": 不在两者之间
    - "in": 在列表中 (value应为一个值列表)
    - "not_in": 不在列表中
    - "is_null": 值为空
    - "is_not_null": 值不为空
- "value": 筛选的值。对于 "between", "in", "not_in" 操作符，value应该是一个列表。对于 "is_null", "is_not_null", value可以省略或为null。

用户数据表的列信息如下 (列名已规范化为小写和下划线)：
{json.dumps(columns_info_dict, ensure_ascii=False, indent=2)}

请确保 "column" 字段的值严格匹配上述列信息中的列名。
如果查询涉及到日期，请尝试将日期转换为 "YYYY-MM-DD" 格式。
如果查询意图不明确或无法转换为筛选条件，请返回一个空的 "filters" 列表。
只返回JSON对象，不要包含任何其他解释或说明。
"""
    user_prompt = f"""请将以下自然语言查询转换为结构化的JSON筛选条件对象:
"{query}"

请根据我上面提供的数据列信息，确保JSON中的"column"字段使用的是列信息中的实际列名。
例如，如果列信息中有 "product_name"，则JSON中应使用 "product_name"，而不是 "产品名称"。
返回的JSON对象格式应为：
{{
  "filters": [
    {{"column": "column_name_from_schema", "operator": "operator_type", "value": "filter_value"}},
    // ... 更多过滤器
  ],
  "logical_operator": "AND" // 或 "OR"
}}
如果查询中没有明确的逻辑操作符（如"和"、"或"），默认为 "AND"。
只返回JSON对象。
"""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"} # Ensure LLM provides JSON
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        assistant_message_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not assistant_message_content:
            logger.warning("硅基流动API响应中未找到 'content'。")
            return {"filters": [], "logical_operator": "AND"}

        # Attempt to parse the content as JSON
        try:
            parsed_conditions = json.loads(assistant_message_content)
        except json.JSONDecodeError as jde:
            logger.error(f"硅基流动API返回的不是有效的JSON: {assistant_message_content}. Error: {jde}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM返回的不是有效的JSON")


        # Validation
        if not isinstance(parsed_conditions, dict) or "filters" not in parsed_conditions or not isinstance(parsed_conditions["filters"], list):
            logger.error(f"LLM返回的JSON结构不符合预期: {parsed_conditions}")
            raise ValueError("LLM返回的JSON结构不符合预期")

        valid_columns = set(columns_info_dict.keys())
        # Filter out invalid conditions more gracefully or log them
        validated_filters = []
        for item in parsed_conditions.get("filters", []):
            if isinstance(item, dict) and item.get("column") in valid_columns and "operator" in item:
                 # 'value' can be legitimately missing for "is_null", "is_not_null"
                if item["operator"] in ["is_null", "is_not_null"] or "value" in item:
                    validated_filters.append(item)
                else:
                    logger.warning(f"Skipping filter due to missing 'value' for operator '{item['operator']}': {item}")
            else:
                logger.warning(f"Skipping invalid filter item from LLM: {item}")

        parsed_conditions["filters"] = validated_filters
        if "logical_operator" not in parsed_conditions or parsed_conditions["logical_operator"] not in ["AND", "OR"]:
            parsed_conditions["logical_operator"] = "AND" # Default or correct

        logger.info(f"硅基流动LLM解析后的筛选条件: {json.dumps(parsed_conditions, ensure_ascii=False)}")
        return parsed_conditions
    except requests.exceptions.RequestException as e:
        logger.error(f"硅_基流动API请求错误: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"硅基流动API请求错误: {e}")
    except (json.JSONDecodeError, ValueError) as e: # Catch ValueError from validation
        logger.error(f"解析硅基流动LLM返回内容失败或内容无效: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"解析LLM响应失败或内容无效: {e}")
    except Exception as e:
        logger.error(f"硅基流动解析查询时发生未知错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM解析时发生未知错误")


def parse_with_ollama(query: str, columns_info_dict: Dict, config: Dict) -> Dict:
    logger.info(f"开始使用Ollama API解析自然语言查询: {query}")
    api_url = config.get('apiUrl', DEFAULT_LLM_CONFIG['ollama']['apiUrl'])
    model = config.get('model', DEFAULT_LLM_CONFIG['ollama']['model'])
    temperature = float(config.get('temperature', DEFAULT_LLM_CONFIG['ollama']['temperature']))
    top_p = float(config.get('topP', DEFAULT_LLM_CONFIG['ollama']['topP']))

    # Use a simplified prompt structure similar to SiliconFlow for consistency
    system_prompt = f"""你是一个专业的数据分析助手。
你的任务是将用户的自然语言查询转换为一个结构化的JSON筛选条件对象。
这个JSON对象应该包含一个 "filters" 列表和一个可选的 "logical_operator" ("AND" 或 "OR", 默认为 "AND")。
"filters" 列表中的每个对象代表一个筛选条件，包含: "column", "operator", "value"。
操作符可以是: "equals", "not_equals", "contains", "not_contains", "greater_than", "less_than", "greater_than_or_equal_to", "less_than_or_equal_to", "between", "not_between", "in", "not_in", "is_null", "is_not_null".
用户数据表的列信息如下 (列名已规范化为小写和下划线)：
{json.dumps(columns_info_dict, ensure_ascii=False, indent=2)}
确保 "column" 字段的值严格匹配上述列信息中的列名。
如果查询涉及到日期，请尝试将日期转换为 "YYYY-MM-DD" 格式。
如果查询意图不明确或无法转换为筛选条件，请返回一个空的 "filters" 列表。
只返回JSON对象，不要包含任何其他解释或说明。
"""
    user_prompt = f"""请将以下自然语言查询转换为结构化的JSON筛选条件对象:
"{query}"
返回的JSON对象格式应为：
{{
  "filters": [
    {{"column": "column_name_from_schema", "operator": "operator_type", "value": "filter_value"}}
  ],
  "logical_operator": "AND"
}}
只返回JSON对象。
"""
    # Ollama settings might come from app.core.settings too
    # system_prompt = settings.SYSTEM_PROMPT
    # user_prompt = settings.USER_PROMPT

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "options": {"temperature": temperature, "top_p": top_p},
        "format": "json", # Ollama native JSON mode
        "stream": False
    }
    try:
        response = requests.post(api_url, json=payload, timeout=60) # Increased timeout for local LLMs
        response.raise_for_status()
        result_text = response.text # Get raw text first for debugging

        try:
            # Ollama with "format": "json" should return a JSON object where 'message.content' contains the JSON string.
            # However, sometimes it might directly return the JSON string if the model is fine-tuned for it,
            # or it might wrap it differently. Let's try to parse the whole response first.
            full_response_json = json.loads(result_text)
            assistant_message_content = full_response_json.get('message', {}).get('content', '')
            if not assistant_message_content: # If message.content is empty, maybe the full response itself is the JSON.
                 assistant_message_content = result_text # Fallback: try parsing the whole text
        except json.JSONDecodeError:
            # If the whole response text isn't JSON, assume it's directly the content string
            assistant_message_content = result_text

        if not assistant_message_content:
            logger.warning("Ollama API响应中未找到 'content' 或内容为空。")
            return {"filters": [], "logical_operator": "AND"}

        parsed_conditions: Dict = {}
        try:
            # The content itself should be a JSON string
            parsed_conditions = json.loads(assistant_message_content)
        except json.JSONDecodeError:
            # Fallback for content that might be wrapped in ```json ... ```
            logger.warning(f"Ollama content was not direct JSON: '{assistant_message_content[:200]}...' Trying to extract.")
            json_match = re.search(r'```json\s*(.*?)\s*```', assistant_message_content, re.DOTALL)
            if json_match:
                parsed_conditions = json.loads(json_match.group(1))
            else:
                # Last resort: try to find any valid JSON object within the string
                json_match = re.search(r'\{[\s\S]*\}', assistant_message_content, re.DOTALL)
                if json_match:
                    parsed_conditions = json.loads(json_match.group(0))
                else:
                    logger.error(f"无法从Ollama API响应中提取有效的JSON: {assistant_message_content}")
                    raise ValueError("无法从Ollama API响应中提取有效的JSON")

        # Validation
        if not isinstance(parsed_conditions, dict) or "filters" not in parsed_conditions or not isinstance(parsed_conditions["filters"], list):
            logger.error(f"LLM返回的JSON结构不符合预期: {parsed_conditions}")
            raise ValueError("LLM返回的JSON结构不符合预期")

        valid_columns = set(columns_info_dict.keys())
        validated_filters = []
        for item in parsed_conditions.get("filters", []):
            if isinstance(item, dict) and item.get("column") in valid_columns and "operator" in item:
                if item["operator"] in ["is_null", "is_not_null"] or "value" in item:
                    validated_filters.append(item)
                else:
                    logger.warning(f"Skipping filter due to missing 'value' for operator '{item['operator']}': {item}")
            else:
                logger.warning(f"Skipping invalid filter item from LLM: {item}")

        parsed_conditions["filters"] = validated_filters
        if "logical_operator" not in parsed_conditions or parsed_conditions["logical_operator"] not in ["AND", "OR"]:
            parsed_conditions["logical_operator"] = "AND"

        logger.info(f"Ollama LLM解析后的筛选条件: {json.dumps(parsed_conditions, ensure_ascii=False)}")
        return parsed_conditions
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API请求错误: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Ollama API请求错误: {e}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"解析Ollama LLM返回内容失败或内容无效: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"解析LLM响应失败或内容无效: {e}")
    except Exception as e:
        logger.error(f"Ollama解析查询时发生未知错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="LLM解析时发生未知错误")

# --- Pandas Filtering Logic (apply_dynamic_filters) ---
# This is almost identical to your Flask app's version.
def apply_dynamic_filters(df: pd.DataFrame, parsed_conditions: Dict) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    if not parsed_conditions or not parsed_conditions.get("filters"): return df.copy()

    filters_list = parsed_conditions["filters"]
    logical_op = parsed_conditions.get("logical_operator", "AND").upper()

    # Initialize total_mask based on logical_op
    if logical_op == "AND":
        total_mask = pd.Series([True] * len(df), index=df.index)
    elif logical_op == "OR":
        total_mask = pd.Series([False] * len(df), index=df.index)
    else: # Default to AND if unknown operator
        total_mask = pd.Series([True] * len(df), index=df.index)
        logger.warning(f"Unknown logical operator '{logical_op}', defaulting to AND.")


    for condition_idx, condition in enumerate(filters_list):
        col, op, val = condition.get("column"), condition.get("operator"), condition.get("value") # val can be None

        if not col or not op or col not in df.columns:
            logger.warning(f"跳过无效或不完整的筛选条件 (索引 {condition_idx}): {condition}")
            continue

        # For "is_null" and "is_not_null", value is not needed.
        if op not in ["is_null", "is_not_null"] and val is None and op not in ["is_null", "is_not_null"]:
            # If value is required but missing, skip this condition.
            # Example: "equals" with no value is meaningless.
            logger.warning(f"Skipping filter condition (索引 {condition_idx}) due to missing 'value' for operator '{op}': {condition}")
            continue

        current_mask = pd.Series([False] * len(df), index=df.index) # Initialize to False, only True rows pass
        series_to_filter = df[col]

        try:
            # Type casting for value based on series dtype and operator
            # This is complex and needs to be robust
            original_series_dtype = series_to_filter.dtype

            # String operations: ensure series is string type for contains/equals on strings
            if op in ["contains", "not_contains"] or \
               (op in ["equals", "not_equals"] and isinstance(val, str)):
                series_to_filter = series_to_filter.astype(str)
                if val is not None: val = str(val)


            is_datetime_col = pd.api.types.is_datetime64_any_dtype(original_series_dtype)
            is_numeric_col_original = pd.api.types.is_numeric_dtype(original_series_dtype) and not is_datetime_col


            # Handle type conversion for 'val' for comparison operators
            if op in ["greater_than", "less_than", "greater_than_or_equal_to", "less_than_or_equal_to", "between", "not_between"]:
                temp_series_for_conversion = series_to_filter.dropna() # Use non-null values for type check

                # Try to convert 'val' to the most appropriate type
                if is_datetime_col or (temp_series_for_conversion.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}').any() and isinstance(val, str)):
                     # If original column is datetime, or if value looks like a date string
                    try:
                        if op in ["between", "not_between"]:
                            if not (isinstance(val, list) and len(val) == 2): raise ValueError("日期 'between' 值应为列表[min, max]")
                            val = [pd.to_datetime(v, errors='coerce') for v in val]
                            if any(pd.isna(v) for v in val): raise ValueError(f"日期 'between' 值解析失败: {condition.get('value')}")
                        else:
                            val = pd.to_datetime(val, errors='coerce')
                            if pd.isna(val): raise ValueError(f"日期值解析失败: {condition.get('value')}")
                        series_to_filter = pd.to_datetime(series_to_filter, errors='coerce') # Coerce series also
                    except Exception as date_err:
                        logger.warning(f"Could not convert value/series to datetime for col '{col}', op '{op}': {date_err}. Skipping filter.")
                        continue
                elif is_numeric_col_original or (isinstance(val, (int, float, str)) and str(val).replace('.', '', 1).isdigit()):
                    # If original column is numeric, or value looks numeric
                    try:
                        if op in ["between", "not_between"]:
                            if not (isinstance(val, list) and len(val) == 2): raise ValueError("数字 'between' 值应为列表[min, max]")
                            val = [pd.to_numeric(v, errors='coerce') for v in val]
                            if any(np.isnan(v) for v in val): raise ValueError(f"数字 'between' 值解析失败: {condition.get('value')}")
                        else:
                            val = pd.to_numeric(val, errors='coerce')
                            if np.isnan(val): raise ValueError(f"数字值解析失败: {condition.get('value')}")
                        series_to_filter = pd.to_numeric(series_to_filter, errors='coerce') # Coerce series also
                    except Exception as num_err:
                        logger.warning(f"Could not convert value/series to numeric for col '{col}', op '{op}': {num_err}. Skipping filter.")
                        continue
                # else: val remains as is, direct comparison will be attempted.

            # Apply filter logic
            if op == "equals": current_mask = (series_to_filter == val)
            elif op == "not_equals": current_mask = (series_to_filter != val)
            elif op == "contains": current_mask = series_to_filter.str.contains(val, case=False, na=False)
            elif op == "not_contains": current_mask = ~series_to_filter.str.contains(val, case=False, na=False)
            elif op == "greater_than": current_mask = (series_to_filter > val)
            elif op == "less_than": current_mask = (series_to_filter < val)
            elif op == "greater_than_or_equal_to": current_mask = (series_to_filter >= val)
            elif op == "less_than_or_equal_to": current_mask = (series_to_filter <= val)
            elif op == "between": current_mask = series_to_filter.between(val[0], val[1], inclusive="both")
            elif op == "not_between": current_mask = ~series_to_filter.between(val[0], val[1], inclusive="both")
            elif op == "in":
                if not isinstance(val, list): val = [val]
                # Ensure values in `val` are of compatible type with the series
                # This can be tricky if `val` contains mixed types or needs conversion.
                # For simplicity, we assume `val` items are already appropriate or `isin` handles it.
                current_mask = series_to_filter.isin(val)
            elif op == "not_in":
                if not isinstance(val, list): val = [val]
                current_mask = ~series_to_filter.isin(val)
            elif op == "is_null": current_mask = series_to_filter.isnull()
            elif op == "is_not_null": current_mask = series_to_filter.notnull()
            else:
                logger.warning(f"未知操作符 (索引 {condition_idx}) '{op}'，跳过条件。")
                continue

            # Combine mask
            if logical_op == "AND":
                total_mask &= current_mask
            elif logical_op == "OR":
                total_mask |= current_mask

        except ValueError as ve: # Catch type conversion errors from above
            logger.warning(f"筛选值或列类型不匹配 (索引 {condition_idx}, 列 '{col}', 操作 '{op}', 值 '{condition.get('value')}'): {str(ve)}. Skipping this filter condition.")
            # If AND, this condition effectively fails. If OR, it doesn't contribute.
            if logical_op == "AND": total_mask &= pd.Series([False] * len(df), index=df.index) # Make it fail safely for AND
            # For OR, it's already initialized to False or previous states.
        except Exception as e:
            logger.error(f"处理筛选条件时发生意外错误 (索引 {condition_idx}, 列 '{col}', 操作 '{op}'): {str(e)}", exc_info=True)
            # Decide how to handle: skip condition or error out? For now, skip.
            if logical_op == "AND": total_mask &= pd.Series([False] * len(df), index=df.index)

    return df[total_mask].copy()