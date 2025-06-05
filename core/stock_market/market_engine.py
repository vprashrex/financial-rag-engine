"""
1. fetch market data from the vantage API
2. process the market data information and generate the summary report
3. updat the vector database with the summary report
"""
from core.vector.vector_interfaces import MarketDataVectorDB
from core.vector.vector_engine import VectorDB
from core.stock_market.fetch_market_data import MarketDataAnalyzer
from logger import stock_logger as logger
from langchain.schema import Document
from uuid import uuid4
from typing import List

class MarketEngine:
    def __init__(self):
        self.market_data_service = MarketDataAnalyzer()
        self.vector_db = VectorDB(MarketDataVectorDB())
    
    def fetch_and_update_market_data(self):
        """
        Fetch market data for a given symbol and update the vector database.
        
        Args:
            symbol: Stock symbol to fetch market data for.
        """
        try:
            # Fetch market data
            market_data = self.market_data_service.fetch_market_data()
            if not market_data:
                logger.error(f"No market data found")
                raise ValueError(f"No market data found")
            
            # Process and generate summary report
            summary_documents = self.market_data_service.generate_summary_report(market_data)
                
            # Update vector database with the summary report
            self.vector_db.update_documents(summary_documents)
            logger.debug(f"Successfully updated vector database with market data")
            return {"status": "success", "code": 200, "message": f"Successfully updated market data"}
        except Exception as e:
            logger.error(f"Error fetching or updating market data: {str(e)}")
            raise
    
    def query_market_data(self, query: str, k: int = 5) -> List[Document]:
        """
        Query market data from the vector database
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of relevant market data documents
        """
        try:
            # Get collection name for logging
            collection_name = self.vector_db.interface.get_collection_name()
            logger.info(f"Querying market data collection: {collection_name}")
            
            # Check if collection exists before querying
            if not self.vector_db.collection_exists():
                logger.warning(f"Market data collection '{collection_name}' does not exist. Try fetching market data first.")
                return []
            
            # Query documents
            results = self.vector_db.query_documents(query, k)
            
            logger.info(f"Retrieved {len(results)} market data documents for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error querying market data: {str(e)}")
            return []