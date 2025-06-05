"""
This script is used to test the retrieval of market data from the MarketEngine.
"""

from core.stock_market.market_engine import MarketEngine
def main():
    market_engine = MarketEngine()
    
    try:
        # Uncomment the line below to fetch and update market data
        # This will fetch the latest market data and update the vector database.
        
        #market_engine.fetch_and_update_market_data()  # Fetch and update market data

        query_key = 'ETH-USD' # Example query key for Ethereum USD market data
        k = 1  # Number of results to return
        query_result = market_engine.query_market_data(query_key, k=k)

        """
        Query result will be a list of Document objects containing the market data.
        Example output:
        [Document(id='7c46f3dd-fcf8-47a3-b0e3-5044f7dc4422', metadata={'timestamp': '2025-06-05', 'id': '2509a686-9502-48e7-98e1-407d739bd2e3', 'symbol': 'ETH-USD'}, page_content='\n## ETH-USD\n- Price: $2614.57\n- Volume: 1,599\n- Daily Change: +0.21%\n\n### Technical Indicators:\n- MA(5): $2593.67\n- MA(20): $2571.27\n- RSI: 45.5\n- Volatility: 36.0%\n- ATR: $110.36\n\nLast Update: 2025-06-05\n')]
        """
        for doc in query_result:
            print("----------------------------------")
            print(f"Document ID: {doc.id}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content: {doc.page_content}\n")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()