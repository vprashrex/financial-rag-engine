from langchain.schema import Document
from abc import ABC, abstractmethod
from typing import List, Optional

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
    
    def __init__(self, chat_id: Optional[str] = None):
        self.chat_id = chat_id
    
    def get_collection_name(self) -> str:
        if self.chat_id:
            return f"market_data_collection_{self.chat_id}"
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
    
    def __init__(self, chat_id: Optional[str] = None):
        self.chat_id = chat_id
    
    def get_collection_name(self) -> str:
        if self.chat_id:
            return f"financial_documents_collection_{self.chat_id}"
        return "financial_documents_collection"
    
    def update_documents(self, documents: List[Document]) -> None:
        """Update financial document documents"""
        # Implementation will be handled by VectorDB class
        pass
    
    def query_documents(self, query: str, k: int = 5) -> List[Document]:
        """Query financial document documents"""
        # Implementation will be handled by VectorDB class
        pass
