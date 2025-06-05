"""
1. connect to financial data and fetch atleast 5 stocks data/cryptos data
2. process incoming data with timestamps and proper data validation
3. calculate moving averages, RSI, volatility metrics.
5. store the processed data in a langchain vector database chromadb
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os

load_dotenv()

class VectorDBInterface(ABC):
    """Abstract interface for vector database operations"""
    
    @abstractmethod
    def update_documents(self, documents: List[Document]) -> None:
        """Update documents in the vector database"""
        pass
    
    @abstractmethod
    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """Query documents from the vector database"""
        pass
    
    @abstractmethod
    def get_collection_name(self) -> str:
        """Get the collection name for this vector database"""
        pass

class MarketDataVectorDB(VectorDBInterface):
    """Vector database for market data (stocks, crypto, technical indicators)"""
    
    def get_collection_name(self) -> str:
        return "market_data_collection"
    
    def update_documents(self, documents: List[Document]) -> None:
        """Update market data documents"""
        # Implementation will be handled by VectorDB class
        pass
    
    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """Query market data documents"""
        # Implementation will be handled by VectorDB class
        pass

class FinancialDocumentVectorDB(VectorDBInterface):
    """Vector database for financial documents (reports, news, analysis)"""
    
    def get_collection_name(self) -> str:
        return "financial_documents_collection"
    
    def update_documents(self, documents: List[Document]) -> None:
        """Update financial document documents"""
        # Implementation will be handled by VectorDB class
        pass
    
    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """Query financial document documents"""
        # Implementation will be handled by VectorDB class
        pass

class VectorDB:
    def __init__(self, db_type: str = "market_data", persist_directory: str = "./chroma_db"):
        """
        Initialize VectorDB with specified type
        
        Args:
            db_type: Either "market_data" or "financial_documents"
            persist_directory: Directory to persist ChromaDB data
        """
        self.embedding = GoogleGenerativeAIEmbeddings(
            model='models/gemini-embedding-exp-03-07',
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        self.persist_directory = persist_directory
        
        # Initialize the appropriate interface based on type
        if db_type == "market_data":
            self.interface = MarketDataVectorDB()
        elif db_type == "financial_documents":
            self.interface = FinancialDocumentVectorDB()
        else:
            raise ValueError("db_type must be either 'market_data' or 'financial_documents'")
        
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
                print(f"Successfully updated {len(documents)} documents in {self.interface.get_collection_name()}")
        except Exception as e:
            print(f"Error updating documents: {str(e)}")
            raise
    
    def query_documents(self, query: str, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Query documents from the vector database
        
        Args:
            query: Search query string
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters
            
        Returns:
            List of relevant Document objects
        """
        try:
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query=query, 
                    k=k, 
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query=query, k=k)
            
            print(f"Retrieved {len(results)} documents for query: '{query}'")
            return results
        except Exception as e:
            print(f"Error querying documents: {str(e)}")
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
            print(f"Retrieved {len(results)} documents with scores for query: '{query}'")
            return results
        except Exception as e:
            print(f"Error querying documents with scores: {str(e)}")
            return []
    
    def delete_collection(self) -> None:
        """Delete the entire collection"""
        try:
            self.vectorstore.delete_collection()
            print(f"Successfully deleted collection: {self.interface.get_collection_name()}")
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection"""
        return {
            "collection_name": self.interface.get_collection_name(),
            "persist_directory": self.persist_directory,
            "embedding_model": "models/gemini-embedding-exp-03-07"
        }

# Example usage:
if __name__ == "__main__":
    # Market Data VectorDB
    market_vdb = VectorDB(db_type="market_data")
    
    # Financial Documents VectorDB
    doc_vdb = VectorDB(db_type="financial_documents")
    
    # Example documents
    sample_market_docs = [
        Document(
            page_content="MSFT stock price: $120.25, RSI: 15.2, MA_20: $198.50",
            metadata={"symbol": "MSFT", "timestamp": "2025-06-04", "type": "market_data"}
        )
    ]
    
    sample_financial_docs = [
        Document(
            page_content="MICROSOFT Q1 2025 earnings report shows strong growth in AI revenue",
            metadata={"company": "MSFT", "document_type": "earnings_report", "date": "2025-06-04"}
        )
    ]
    
    # Update documents
    market_vdb.update_documents(sample_market_docs)
    doc_vdb.update_documents(sample_financial_docs)
    
    # Query documents
    market_results = market_vdb.query_documents("MSFT RSI technical indicators")
    print("Market Data Query Results:")
    if market_results:
        for doc in market_results:
            print(doc.page_content, doc.metadata)
    doc_results = doc_vdb.query_documents("MSFT earnings revenue growth")
    print("Financial Documents Query Results:")
    if doc_results:
        for doc in doc_results:
            print(doc.page_content, doc.metadata)