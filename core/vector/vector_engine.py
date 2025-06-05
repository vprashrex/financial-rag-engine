#from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import os
from core.vector.vector_interfaces import VectorDBInterface
from logger import vector_logger as logger

load_dotenv()

class VectorDB:
    def __init__(self, db_type: VectorDBInterface, persist_directory: str = "./chroma_db"):
        """
        Initialize VectorDB with specified type
        
        Args:
            db_type: Either "market_data" or "financial_documents"
            persist_directory: Directory to persist ChromaDB data
        """
        self.embedding = NVIDIAEmbeddings(
            model='NV-Embed-QA',
            api_key=os.getenv('NVIDIA_API_KEY'),
            truncate='NONE'
        )
        
        self.persist_directory = persist_directory
        
        # Initialize the appropriate interface based on type
        try:
            self.interface = db_type
        except Exception as e:
            logger.error(f"Failed to initialize vector database interface: {str(e)}")   
            return
            
        # Initialize ChromaDB with collection name
        self.vectorstore = self._initialize_vectorstore()
    
    def _initialize_vectorstore(self) -> Chroma:
        """Initialize ChromaDB vectorstore with appropriate collection"""
        return Chroma(
            collection_name=self.interface.get_collection_name(),
            embedding_function=self.embedding,
            persist_directory=self.persist_directory
        )
    
    def update_documents(self, documents: List[Document]) -> None:
        """
        Update documents in the vector database
        
        Args:
            documents: List of LangChain Document objects to add/update
        """
        try:
            if documents:
                # Add documents to the vectorstore
                self.vectorstore.add_documents(documents)
                logger.debug(f"Successfully updated {len(documents)} documents in {self.interface.get_collection_name()}")
        except Exception as e:
            logger.error(f"Error updating documents: {str(e)}")
            raise
    
    

    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """
        Query documents from the vector database
        
        Args:
            query: Search query string
            k: Number of documents to retrieve
        
        Returns:
            List of relevant Document objects
        """
        try:
            # Check if collection exists
            if not self.collection_exists():
                logger.warning(f"Cannot query documents: Collection '{self.interface.get_collection_name()}' does not exist")
                return []
            
            # Ensure we're using the correct collection
            collection_name = self.interface.get_collection_name()
                        
            # Simple query without filters
            results = self.vectorstore.similarity_search(query=query, k=k)
            
            logger.info(f"Retrieved {len(results)} documents from collection '{collection_name}' for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error querying documents from collection '{self.interface.get_collection_name()}': {str(e)}")
            return []
    
    def query_market_data(self, query: str, k: int = 5):
        """
        Query market data from the vector database
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of relevant market data documents
        """
        try:
            # Check if collection exists
            if not self.vector_db.collection_exists():
                logger.warning("No market data collection found. Try fetching market data first.")
                return []
                
            return self.vector_db.query_documents(query, k)
        except Exception as e:
            logger.error(f"Error querying market data: {str(e)}")
            return []
    
    def query_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Query documents with similarity scores
        
        Args:
            query: Search query string
            k: Number of documents to retrieve
            
        Returns:
            List of tuples (Document, score)
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query=query, k=k)
            logger.debug(f"Retrieved {len(results)} documents with scores for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error querying documents with scores: {str(e)}")
            return []
    
    def delete_collection(self) -> None:
        """Delete the entire collection"""
        try:
            self.vectorstore.delete_collection()
            logger.debug(f"Successfully deleted collection: {self.interface.get_collection_name()}")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection"""
        return {
            "collection_name": self.interface.get_collection_name(),
            "persist_directory": self.persist_directory,
            "embedding_model": "models/gemini-embedding-exp-03-07"
        }

    def collection_exists(self) -> bool:
        """
        Check if the collection exists in the ChromaDB
        
        Returns:
            Boolean indicating if the collection exists
        """
        try:
            collection_name = self.interface.get_collection_name()
            
            # Get Chroma client from the vectorstore
            chroma_client = self.vectorstore._client
            
            # List all collections
            collection_names = [col.name for col in chroma_client.list_collections()]
            
            # Check if our collection exists
            exists = collection_name in collection_names
            
            if exists:
                logger.debug(f"Collection '{collection_name}' exists")
            else:
                logger.warning(f"Collection '{collection_name}' does not exist")
                
            return exists
        except Exception as e:
            logger.error(f"Error checking if collection exists: {str(e)}")
            return False
    
  