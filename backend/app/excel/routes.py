from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any # Added Dict, Any
import pandas as pd
from io import BytesIO
import numpy as np
import json
from pathlib import Path
from sqlmodel import Session
from pydantic import BaseModel # Ensure BaseModel is imported if used for internal dicts

from app.excel import models as excel_models, processing as excel_logic
from app.database.models import User as DBUser, UploadedExcelFile as DBUploadedExcelFile
from app.database.setup import get_db
from app.core.dependencies import get_current_active_user

router = APIRouter()

@router.post("/upload", response_model=excel_models.FileUploadResponse) # Using the pydantic response model
async def upload_excel_files_route(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    actual_files = [f for f in files if f.filename]
    if not actual_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid files with filenames provided.")

    if not current_user.user_group_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to a group. Cannot upload files.")

    # Use the new processing function
    saved_db_records, processing_errors = await excel_logic.save_original_files_and_create_records(
        db=db,
        files=actual_files,
        uploader=current_user
    )

    response_details: List[excel_models.FileUploadResponseItem] = []
    for db_record in saved_db_records:
        response_details.append(
            excel_models.FileUploadResponseItem(
                original_filename=db_record.original_filename,
                stored_server_filename=Path(db_record.stored_file_path).name, # Get filename from path
                stored_path=db_record.stored_file_path,
                size_bytes=db_record.file_size_bytes or 0, # Ensure size is not None
                mime_type=db_record.mime_type,
                db_record_id=db_record.id,
                message="File saved successfully."
            )
        )

    success = len(response_details) > 0

    return excel_models.FileUploadResponse(
        success=success,
        details=response_details,
        errors=processing_errors
    )

@router.post("/query", response_model=excel_models.QueryExecutionResponse)
async def execute_excel_query_route(
    request_data: excel_models.ExcelQueryRequest, # This request might need a file_id
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    if not current_user.user_group_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to a group.")

    # --- CRITICAL CHANGE: How do you select which file to query? ---
    # Option 1: Request_data includes a file_id_to_query
    # file_id_to_query = request_data.file_id_to_query
    # if not file_id_to_query:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_id_to_query is required.")
    # file_record_to_query: Optional[DBUploadedExcelFile] = db.get(DBUploadedExcelFile, file_id_to_query)
    # if not file_record_to_query or file_record_to_query.user_group_id != current_user.user_group_id:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or access denied.")

    # Option 2: Query the LATEST uploaded file for the group (simpler, but less flexible)
    group_files: List[DBUploadedExcelFile] = excel_logic.get_excel_files_for_group(db, current_user.user_group_id, limit=1)
    if not group_files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for your group. Please upload files first.")
    file_record_to_query = group_files[0]
    # --- END CRITICAL CHANGE ---

    try:
        # Now using stored_file_path of the specific original file
        data_to_query_df = excel_logic.read_and_prepare_dataframe_from_file(file_record_to_query.stored_file_path)
    except FileNotFoundError:
        excel_logic.logger.error(f"Data file missing for record ID {file_record_to_query.id}: {file_record_to_query.stored_file_path}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data file not found on server.")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing data file: {str(ve)}")

    # original_filenames_list will now be just the one file being queried
    original_filenames_list = [file_record_to_query.original_filename]

    if data_to_query_df.empty:
        return excel_models.QueryExecutionResponse(
            query=request_data.query,
            parsed_conditions={"filters": [], "logical_operator": "AND"},
            results=[],
            source_files=original_filenames_list
        )

    # Generate columns_info for THIS specific DataFrame
    # (DBUploadedExcelFile model does not store columns_info_json for each original in this simplified setup)
    columns_info = excel_logic.generate_columns_info(data_to_query_df)
    if not columns_info: # Handle case where DataFrame might be empty or have no columns after read
        excel_logic.logger.warning(f"No column information could be generated for file: {file_record_to_query.original_filename}")
        # Depending on LLM, you might need to raise an error or return empty parsed_conditions
        # For now, proceed with empty columns_info, LLM might handle it or fail gracefully.

    # ... (LLM configuration and parsing logic remains similar but acts on 'columns_info' from the single DF) ...
    llm_req_config = request_data.config
    effective_llm_config = json.loads(json.dumps(excel_logic.DEFAULT_LLM_CONFIG))

    if llm_req_config:
        if llm_req_config.apiType:
            effective_llm_config["apiType"] = llm_req_config.apiType
        if llm_req_config.siliconflow:
            sf_conf_dict = llm_req_config.siliconflow.model_dump(exclude_none=True)
            effective_llm_config["siliconflow"].update(sf_conf_dict)
        if llm_req_config.ollama:
            ol_conf_dict = llm_req_config.ollama.model_dump(exclude_none=True)
            effective_llm_config["ollama"].update(ol_conf_dict)

    api_type_to_use = effective_llm_config["apiType"]
    provider_specific_config = effective_llm_config.get(api_type_to_use, {})
    if not provider_specific_config and api_type_to_use in ["siliconflow", "ollama"]:
        provider_specific_config = effective_llm_config.get(api_type_to_use.lower(), {})

    try:
        if api_type_to_use == 'siliconflow':
            parsed_conditions = excel_logic.parse_with_siliconflow(request_data.query, columns_info, provider_specific_config)
        elif api_type_to_use == 'ollama':
            parsed_conditions = excel_logic.parse_with_ollama(request_data.query, columns_info, provider_specific_config)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported API type: {api_type_to_use}")
    except HTTPException as e:
        raise e
    except Exception as e:
        excel_logic.logger.error(f"Unhandled error during LLM parsing: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error parsing query via LLM: {str(e)}")

    filtered_df = excel_logic.apply_dynamic_filters(data_to_query_df, parsed_conditions)

    df_for_json = filtered_df.copy()
    for col_name in df_for_json.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]', 'datetimetz']):
        df_for_json[col_name] = df_for_json[col_name].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
    df_for_json = df_for_json.replace({np.nan: None, pd.NaT: None})
    results_list = df_for_json.to_dict('records')

    return excel_models.QueryExecutionResponse(
        query=request_data.query,
        parsed_conditions=parsed_conditions,
        results=results_list,
        source_files=original_filenames_list # Will be the single file name
    )


@router.post("/download")
async def download_excel_results_route(
    request_data: excel_models.ExcelDownloadRequest,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    if not current_user.user_group_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to a group.")

    # Assuming you want to download results based on the LATEST uploaded file for the group
    group_excel_files_db: List[DBUploadedExcelFile] = excel_logic.get_excel_files_for_group(db, current_user.user_group_id, limit=1)
    if not group_excel_files_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for your group to download.")

    latest_file_record = group_excel_files_db[0] # This is an instance of DBUploadedExcelFile

    try:
        # --- CHANGE HERE ---
        # Use stored_file_path for the original uploaded file
        data_to_filter_df = excel_logic.read_and_prepare_dataframe_from_file(latest_file_record.stored_file_path)
    except FileNotFoundError:
        # --- CHANGE HERE (optional, for consistent logging) ---
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data file not found on server for download.")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing data file for download: {str(ve)}")
    except Exception as e:
         # --- CHANGE HERE (optional, for consistent logging) ---
         excel_logic.logger.error(f"Unexpected error reading data file {latest_file_record.stored_file_path} for download: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error processing data file for download: {str(e)}")


    if data_to_filter_df.empty:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data file is empty after reading. Cannot download.")

    parsed_conditions_for_download = request_data.parsed_conditions
    filename_suffix = Path(latest_file_record.original_filename).stem # Use original filename stem for download

    if not parsed_conditions_for_download and request_data.query:
        # Generate columns_info for THIS specific DataFrame if query needs parsing
        columns_info = excel_logic.generate_columns_info(data_to_filter_df)
        if not columns_info:
            excel_logic.logger.warning(f"No column information for LLM for file: {latest_file_record.original_filename}")
            # Decide how to handle: perhaps download unfiltered if no columns_info for LLM

        # ... (LLM configuration and parsing logic - no change needed here) ...
        llm_req_config = request_data.config
        effective_llm_config = json.loads(json.dumps(excel_logic.DEFAULT_LLM_CONFIG))

        if llm_req_config:
            if llm_req_config.apiType:
                effective_llm_config["apiType"] = llm_req_config.apiType
            if llm_req_config.siliconflow:
                sf_conf_dict = llm_req_config.siliconflow.model_dump(exclude_none=True)
                effective_llm_config["siliconflow"].update(sf_conf_dict)
            if llm_req_config.ollama:
                ol_conf_dict = llm_req_config.ollama.model_dump(exclude_none=True)
                effective_llm_config["ollama"].update(ol_conf_dict)

        api_type_to_use = effective_llm_config["apiType"]
        provider_specific_config = effective_llm_config.get(api_type_to_use, {})
        if not provider_specific_config and api_type_to_use in ["siliconflow", "ollama"]:
            provider_specific_config = effective_llm_config.get(api_type_to_use.lower(), {})

        try:
            if api_type_to_use == 'siliconflow':
                parsed_conditions_for_download = excel_logic.parse_with_siliconflow(request_data.query, columns_info, provider_specific_config)
            elif api_type_to_use == 'ollama':
                parsed_conditions_for_download = excel_logic.parse_with_ollama(request_data.query, columns_info, provider_specific_config)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported API type for download parsing: {api_type_to_use}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error parsing query for download: {str(e)}")

    if not parsed_conditions_for_download or not parsed_conditions_for_download.get("filters"):
        filtered_df_for_download = data_to_filter_df.copy()
        filename_suffix += "_full_data" # Append to original filename stem
    else:
        filtered_df_for_download = excel_logic.apply_dynamic_filters(data_to_filter_df, parsed_conditions_for_download)
        filename_suffix += "_query_results" # Append to original filename stem

    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_df_for_download.to_excel(writer, sheet_name='Query_Results', index=False)
        output.seek(0)
    except Exception as e:
        excel_logic.logger.error(f"Error writing Excel file for download: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error generating Excel file for download.")

    download_filename = f'{filename_suffix}_{pd.Timestamp.now().strftime("%Y%m%d%H%M%S")}.xlsx'

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{download_filename}"'}
    )

@router.get("/files", response_model=List[excel_models.UploadedExcelFileResponse])
async def list_group_excel_files_route(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user),
    limit: int = 20
):
    if not current_user.user_group_id:
        return []
    files_from_db = excel_logic.get_excel_files_for_group(db, current_user.user_group_id, limit=limit)
    response_list = []
    for db_file in files_from_db:
        # Ensure your excel_api_models.UploadedExcelFileResponse matches the DBUploadedExcelFile structure
        # from app.database.models
        api_response_item = excel_models.UploadedExcelFileResponse.model_validate(db_file)
        response_list.append(api_response_item)
    return response_list