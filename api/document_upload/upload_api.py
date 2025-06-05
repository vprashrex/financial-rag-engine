from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Query
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
from logger import api_logger as logger
from fastapi import status
from core.document_analyzer.document_engine import DocumentEngine
from memory.conv_memory import (
    save_document_message,
    get_list_of_documents
)

router = APIRouter()

UPLOAD_DIRECTORY = "uploads"
ALLOWED_CONTENT_TYPES = ["application/pdf"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure main upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.post("/upload/{chat_id}")
async def upload_pdf(
    chat_id: str = Path(..., description="The ID of the chat"),
    file: UploadFile = File(..., description="PDF file to upload")
):
    """
    Upload a PDF file associated with a specific chat ID.
    
    Args:
        chat_id: Unique identifier for the chat
        file: PDF file to be uploaded (max 10MB)
    
    Returns:
        JSON response with file information or error message
    """
    logger.info(f"File upload request received for chat_id: {chat_id}")
    
    try:
        # Validate file is provided
        if not file:
            logger.warning(f"No file provided for chat_id: {chat_id}")
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Log file details
        logger.debug(f"Received file: {file.filename}, content_type: {file.content_type}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(f"Invalid file type: {file.content_type} for chat_id: {chat_id}")
            raise HTTPException(
                status_code=400, 
                detail=f"Only PDF files are allowed. Received: {file.content_type}"
            )
        
        # Create a chat-specific directory
        chat_directory = os.path.join(UPLOAD_DIRECTORY, chat_id)
        os.makedirs(chat_directory, exist_ok=True)
        
        # Use original filename
        filename = file.filename
        file_path = os.path.join(chat_directory, filename)
        
        # Save the file
        logger.debug(f"Saving file to {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Close the file
        await file.close()
        
        # Save document message to memory
        await save_document_message(
            chat_id=chat_id,
            document_data={
                "name": filename,
                "size": os.path.getsize(file_path)
            }
        )

        logger.info(f"File successfully uploaded for chat_id: {chat_id}, saved as: {file_path}")
        
        # Initialize document engine with chat_id
        doc_engine = DocumentEngine(chat_id=chat_id)
        
        # Process the uploaded PDF
        result = doc_engine.process_and_store_pdf(file_path)
        
        # Add vector processing results to the response
        response_data = {
            "status": "success",
            "message": "File uploaded and processed successfully",
            "data": {
                "chat_id": chat_id,
                "filename": filename,
                "file_path": file_path,
                "content_type": file.content_type,
                "vector_processing": result
            }
        }
        
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=response_data)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions as they are already formatted correctly
        raise
    
    except Exception as e:
        # Log unexpected errors
        error_message = str(e)
        logger.error(f"Error uploading file for chat_id {chat_id}: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading the file: {error_message}"
        )
    
@router.get("/documents/{chat_id}")
async def get_documents(
    chat_id: str = Path(..., description="The ID of the chat")
):
    """
    Retrieve a list of documents associated with a specific chat ID.
    
    Args:
        chat_id: Unique identifier for the chat
    
    Returns:
        JSON response with list of documents or error message
    """
    logger.info(f"Retrieving documents for chat_id: {chat_id}")
    
    try:
        # Fetch list of documents from memory
        documents = await get_list_of_documents(chat_id=chat_id)
        
        if not documents:
            logger.warning(f"No documents found for chat_id: {chat_id}")
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "No documents found"})
        
        logger.info(f"Found {len(documents)} documents for chat_id: {chat_id}")
        
        return JSONResponse(status_code=status.HTTP_200_OK, content={"documents": documents})
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error retrieving documents for chat_id {chat_id}: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving documents: {error_message}"
        )