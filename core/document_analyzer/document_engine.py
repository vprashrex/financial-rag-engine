"""
An utility module for embedding and storing uploaded document in vectordb.
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_cloud_services import LlamaParse
from dotenv import load_dotenv
from core.vector.vector_engine import VectorDB
from core.vector.vector_interfaces import FinancialDocumentVectorDB
from logger import vector_logger as logger

load_dotenv()

class DocumentEngine:
    """Engine for parsing and storing documents in vector database"""
    
    def __init__(self, chat_id: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize DocumentEngine
        
        Args:
            chat_id: Unique identifier for the chat
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.chat_id = chat_id
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize LlamaParse
        self.parser = LlamaParse(
            api_key=os.getenv('LLAMA_PARSE_KEY'),
            result_type="markdown",  # Output as markdown for better structure
            verbose=True
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        
        # Initialize vector database
        self.initialize_vector_db()

    def initialize_vector_db(self, persist_directory: Optional[str] = None) -> None:
        # Create chat-specific persistence directory if not provided
        if not persist_directory:
            persist_directory = f"./financial_documents_db/{self.chat_id}"
        
        # Initialize vector database with financial documents interface
        try:
            # Create chat-specific interface
            db_interface = FinancialDocumentVectorDB(chat_id=self.chat_id)
            
            self.vector_db = VectorDB(
                db_type=db_interface,
                persist_directory=persist_directory
            )
            logger.info(f"Initialized vector DB for chat_id: {self.chat_id} in {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database for chat_id {self.chat_id}: {str(e)}")
            raise
    
    def parse_pdf(self, file_path: str) -> str:
        """
        Parse PDF document using LlamaParse
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Parsed text content
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Starting to parse PDF for chat_id {self.chat_id}: {file_path}")
            
            # Parse the document
            documents = self.parser.load_data(file_path)
            
            # Extract text from parsed documents
            parsed_text = ""
            for doc in documents:
                parsed_text += doc.text + "\n\n"
            
            logger.info(f"Successfully parsed PDF for chat_id {self.chat_id}: {file_path}")
            return parsed_text
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path} for chat_id {self.chat_id}: {str(e)}")
            raise
    
    def create_chunks(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Split text into chunks and create Document objects
        
        Args:
            text: Text content to split
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of Document objects
        """
        try:
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)
            
            # Create Document objects
            documents = []
            for i, chunk in enumerate(text_chunks):
                chunk_metadata = {
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "chunk_size": len(chunk),
                    "chat_id": self.chat_id  # Add chat_id to metadata
                }
                
                # Add additional metadata if provided
                if metadata:
                    chunk_metadata.update(metadata)
                
                doc = Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            logger.info(f"Created {len(documents)} document chunks for chat_id {self.chat_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error creating chunks for chat_id {self.chat_id}: {str(e)}")
            raise
    
    def process_and_store_pdf(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete pipeline: parse PDF, create chunks, and store in vector database
        
        Args:
            file_path: Path to the PDF file
            metadata: Optional metadata to attach to document chunks
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract filename for metadata
            filename = Path(file_path).name
            file_metadata = {
                "source": file_path,
                "filename": filename,
                "document_type": "pdf",
                "chat_id": self.chat_id  # Add chat_id to metadata
            }
            
            # Merge with provided metadata
            if metadata:
                file_metadata.update(metadata)
            
            # Parse PDF
            logger.info(f"Processing PDF for chat_id {self.chat_id}: {filename}")
            parsed_text = self.parse_pdf(file_path)
            
            # Create chunks
            documents = self.create_chunks(parsed_text, file_metadata)
            self.vector_db.update_documents(documents)
            
            result = {
                "success": True,
                "filename": filename,
                "chat_id": self.chat_id,
                "total_chunks": len(documents),
                "total_characters": len(parsed_text),
                "collection_name": self.vector_db.interface.get_collection_name()
            }
            
            logger.info(f"Successfully processed and stored PDF for chat_id {self.chat_id}: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path} for chat_id {self.chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": Path(file_path).name if file_path else "unknown",
                "chat_id": self.chat_id
            }
    
    def process_multiple_pdfs(self, file_paths: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files
        
        Args:
            file_paths: List of PDF file paths
            metadata: Optional metadata to attach to all documents
            
        Returns:
            List of processing results for each file
        """
        results = []
        
        for file_path in file_paths:
            result = self.process_and_store_pdf(file_path, metadata)
            results.append(result)
        
        return results
    
    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        Query stored documents from the chat-specific collection
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        # Log which collection we're querying
        collection_name = self.vector_db.interface.get_collection_name()
        logger.info(f"Querying collection: {collection_name} for chat_id: {self.chat_id}")
        
        # Query without filter_dict, relying on collection isolation
        return self.vector_db.query_documents(query, k)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection"""
        info = self.vector_db.get_collection_info()
        info["chat_id"] = self.chat_id
        return info
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        self.vector_db.delete_collection()
        logger.info(f"Cleared document collection for chat_id {self.chat_id}")