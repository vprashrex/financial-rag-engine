"""
sqlite database for storing chat messages.
"""
import sqlite3
import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "conversations.db"

class SQLiteConversationMemory:
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the SQLite conversation memory."""
        self.db_path = db_path
        
        if not os.path.exists(DB_PATH):
            logger.info(f"Database {db_path} does not exist. Initializing...")
            self.init_db()
    
    def init_db(self):
        """Initialize the SQLite database if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create chats table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                ''')
                
                # Create messages table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (chat_id) REFERENCES chats (id)
                )
                ''')
                
                # Create documents table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    name TEXT,
                    size INTEGER,
                    uploaded_at TEXT,
                    FOREIGN KEY (chat_id) REFERENCES chats (id)
                )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def create_chat(self, chat_id: Optional[str] = None, title: str = "New Chat") -> str:
        """Create a new chat session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if not chat_id:
                    chat_id = str(uuid.uuid4())
                
                now = datetime.utcnow().isoformat() + "Z"
                
                cursor.execute(
                    "INSERT INTO chats (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (chat_id, title, now, now)
                )
                
                conn.commit()
                logger.info(f"Created new chat with ID: {chat_id}")
                return chat_id
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            raise
    
    def save_message(self, chat_id: str, role: Literal['user', 'model', 'tool'], content: str) -> bool:
        """
        Save a message to the conversation history.
        
        Args:
            chat_id (str): The chat ID
            role (str): The role of the message sender (user, model, tool)
            content (str): The content of the message
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if chat exists
                cursor.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
                chat = cursor.fetchone()
                
                # Create chat if it doesn't exist
                if not chat:
                    self.create_chat(chat_id)
                
                now = datetime.utcnow().isoformat() + "Z"
                
                # Insert message
                cursor.execute(
                    "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                    (chat_id, role, content, now)
                )
                
                # Update chat's updated_at timestamp
                cursor.execute(
                    "UPDATE chats SET updated_at = ? WHERE id = ?",
                    (now, chat_id)
                )
                
                conn.commit()
                logger.info(f"{role.capitalize()} message saved for chat {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def save_document_message(self, chat_id: str, document_data: Dict[str, Any]) -> bool:
        """
        Save document information to a chat.
        
        Args:
            chat_id (str): The chat ID
            document_data (dict): Dictionary containing document metadata with keys:
                - name: file name
                - size: file size in bytes
                
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if chat exists
                cursor.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
                chat = cursor.fetchone()
                
                # Create chat if it doesn't exist
                if not chat:
                    self.create_chat(chat_id)
                
                now = datetime.utcnow().isoformat() + "Z"
                
                # Insert document
                cursor.execute(
                    "INSERT INTO documents (chat_id, name, size, uploaded_at) VALUES (?, ?, ?, ?)",
                    (chat_id, document_data.get('name', ''), document_data.get('size', 0), now)
                )
                
                # Update chat's updated_at timestamp
                cursor.execute(
                    "UPDATE chats SET updated_at = ? WHERE id = ?",
                    (now, chat_id)
                )
                
                conn.commit()
                logger.info(f"Document '{document_data.get('name', '')}' saved for chat {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False
    
    def load_context(self, chat_id: str, n: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch the messages from a chat.
        
        Args:
            chat_id (str): The chat ID
            n (int): The number of most recent messages to fetch (0 for all)
            
        Returns:
            list: The chat messages
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if n > 0:
                    # Get the last n messages by ordering DESC and limiting, then reverse to chronological order
                    query = "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT ?"
                    cursor.execute(query, (chat_id, n))
                    rows = cursor.fetchall()
                    rows = list(reversed(rows))  # Reverse to get chronological order
                else:
                    query = "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp"
                    cursor.execute(query, (chat_id,))
                    rows = cursor.fetchall()
                
                messages = ""
                for row in rows:
                    if row['role'] == 'user':
                        messages += "----------------------------------------\n"
                    messages += f"{row['role']}: {row['content']}\n"
                messages = messages.strip()  # Remove trailing newline                
                return messages
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return []
    
    def load_chat_history(self, chat_id: str) -> List[Dict[str, str]]:
        """
        Load the complete chat history. Same as load_context but returns all messages.
        
        Args:
            chat_id (str): The chat ID
            
        Returns:
            list: The complete chat history
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp"
                cursor.execute(query, (chat_id,))
                rows = cursor.fetchall()
                
                messages = []
                for row in rows:
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    })
                
                logger.info(f"Loaded {len(messages)} messages for chat {chat_id}")
                return messages
        except Exception as e:
            logger.error(f"Error loading chat history : {e}")
            return []
    
    def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """
        Get information about a chat including messages and documents.
        
        Args:
            chat_id (str): The chat ID
            
        Returns:
            dict: The chat information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get chat info
                cursor.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
                chat_row = cursor.fetchone()
                
                if not chat_row:
                    logger.warning(f"Chat {chat_id} not found")
                    return {}
                
                chat_info = dict(chat_row)
                
                # Get messages
                cursor.execute("SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY timestamp", (chat_id,))
                message_rows = cursor.fetchall()
                
                messages = []
                for row in message_rows:
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"]
                    })
                
                chat_info["messages"] = messages
                
                # Get documents
                cursor.execute("SELECT name, size, uploaded_at FROM documents WHERE chat_id = ? ORDER BY uploaded_at", (chat_id,))
                document_rows = cursor.fetchall()
                
                documents = []
                for row in document_rows:
                    documents.append({
                        "name": row["name"],
                        "size": row["size"],
                        "uploaded_at": row["uploaded_at"]
                    })
                
                if documents:
                    chat_info["document"] = documents
                
                return chat_info
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
            return {}
    
    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat and all its messages and documents.
        
        Args:
            chat_id (str): The chat ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete messages
                cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
                
                # Delete documents
                cursor.execute("DELETE FROM documents WHERE chat_id = ?", (chat_id,))
                
                # Delete chat
                cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
                
                conn.commit()
                logger.info(f"Deleted chat {chat_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return False
    
    def get_all_chats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all chats with their information.
        
        Returns:
            dict: Dictionary of chat IDs to chat info
        """
        try:
            result = {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM chats ORDER BY updated_at DESC")
                chat_rows = cursor.fetchall()
                
                for row in chat_rows:
                    chat_id = row["id"]
                    chat_info = self.get_chat_info(chat_id)
                    result[chat_id] = chat_info
            
            return result
        except Exception as e:
            logger.error(f"Error getting all chats: {e}")
            return {}
    
    def get_list_of_documents(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get a list of documents associated with a chat.
        
        Args:
            chat_id (str): The chat ID
            
        Returns:
            list: List of document metadata
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT name, size, uploaded_at FROM documents WHERE chat_id = ? ORDER BY uploaded_at", (chat_id,))
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    documents.append({
                        "name": row["name"],
                        "size": row["size"],
                        "uploaded_at": row["uploaded_at"]
                    })
                
                return documents
        except Exception as e:
            logger.error(f"Error getting documents for chat {chat_id}: {e}")
            return []
  
    

# Create a singleton instance
MEMORY = SQLiteConversationMemory()

async def save_message_memory(chat_id: str, content: str, role: Literal['user', 'model']):
    """
    Save a message to the conversation memory.
    
    Args:
        chat_id (str): The chat ID
        content (str): The message content
        role (str): The role of the message sender (user or model)
    """
    try:
        MEMORY.save_message(chat_id=chat_id, role=role, content=content)
    except Exception as e:
        logger.error(f"Error saving message for chat_id={chat_id}: {e}")

async def save_document_message(chat_id: str, document_data: Dict[str, Any]):
    """
    Save document information to a chat.
    
    Args:
        chat_id (str): The chat ID
        document_data (dict): Dictionary containing document metadata with keys:
            - name: file name
            - size: file size in bytes
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        return MEMORY.save_document_message(chat_id=chat_id, document_data=document_data)
    except Exception as e:
        logger.error(f"Error saving document for chat_id={chat_id}: {e}")
        return False
        

async def load_context(chat_id: str, n: int = 10):
    """
    Load the conversation context.
    
    Args:
        chat_id (str): The chat ID
        n (int): Number of messages to load
    
    Returns:
        list: The conversation messages
    """
    try:
        return MEMORY.load_context(chat_id=chat_id, n=n)
    except Exception as e:
        logger.error(f"Error loading context for chat_id={chat_id}: {e}")
        return []

async def load_chat_history(chat_id: str):
    """
    Load the full chat history.
    
    Args:
        chat_id (str): The chat ID
    
    Returns:
        list: The chat history
    """
    try:
        return MEMORY.load_chat_history(chat_id=chat_id)
    except Exception as e:
        logger.error(f"Error loading chat history for chat_id={chat_id}: {e}")
        return []

async def get_all_chats() -> Dict[str, Dict[str, Any]]:
    """
    Get all chats with their information.
    
    Returns:
        dict: Dictionary of chat IDs to chat info
    """
    try:
        return MEMORY.get_all_chats()
    except Exception as e:
        logger.error(f"Error getting all chats: {e}")
        return {}    

async def get_list_of_documents(chat_id: str) -> List[Dict[str, Any]]:
    """
    Get a list of documents associated with a chat.
    
    Args:
        chat_id (str): The chat ID
        
    Returns:
        list: List of document metadata
    """
    try:
        return MEMORY.get_list_of_documents(chat_id=chat_id)
    except Exception as e:
        logger.error(f"Error getting documents for chat_id={chat_id}: {e}")
        return []

def init_db():
    """Initialize the SQLite database if it doesn't exist."""
    MEMORY.init_db()