"""Chat API module for handling chat-related endpoints."""
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
# default mode : LLM + Agent + RAG
from core.llm_rag_agent.llm import GenaiChat

# uncomment the below line to just use the LLM + RAG only
#from core.llm_rag.llm import GenaiChat

# Conv memory
from memory.conv_memory import (
    load_chat_history,
    get_all_chats
)

from logger import api_logger as logger

router = APIRouter()

# Initialize the GenaiChat instance
genai_chat = GenaiChat()

@router.get("/history")
async def get_chat_history():
    """
    Retrieve chat history.
    
    Returns:
        List of chat messages.
    """
    try:
        chat_history = await get_all_chats()
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve chat history."}
        )
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Chat history retrieved successfully.",
            "history": chat_history
        }
    )

@router.get("/history/{chat_id}")
async def get_chat_history_by_id(chat_id: str):
    """
    Retrieve chat history by chat ID.
    
    Args:
        chat_id: The ID of the chat to retrieve history for.
        
    Returns:
        List of chat messages for the specified chat ID.
    """
    try:
        chat_history = await load_chat_history(chat_id)
    except Exception as e:
        logger.error(f"Error retrieving chat history for chat_id {chat_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to retrieve chat history for chat_id {chat_id}."}
        )
    return JSONResponse(
        status_code=200,
        content={
            "message": "Chat history retrieved successfully.",
            "chat_id": chat_id,
            "history": chat_history
        }
    )

@router.post("/usermessage/{chat_id}")
async def handle_user_message(chat_id: str, message: str):
    """
    Process a user message.
    
    Args:
        chat_id: The ID of the chat to which the message belongs.
        message: The user's message to process.
        
    Returns:
        Response indicating the result of processing the message.
    """
    if not message:
        return JSONResponse(
            status_code=400,
            content={"error": "Message cannot be empty."}
        )
    
    try:
        # Record start time
        start_time = time.time()
        
        # Generate user content based on the message
        user_content = await genai_chat.generate(message, chat_id)
        
        # Calculate duration
        duration = time.time() - start_time
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process message: {str(e)}"}
        )
    
    # Return the generated user content with response time
    return JSONResponse(
        status_code=200,
        content={
            "message": "User message processed successfully.", 
            "content": user_content,
            "metadata": {
                "time_taken":round(duration, 2)
            }
        }
    )
    

