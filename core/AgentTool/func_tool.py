"""
This module contains function definitions for various tasks.
Run retriever to fetch the relevant information from the vector database,
including both Document VectorDB and Financial Stock Market VectorDB based on user query and return the relevant information.
"""

from core.document_analyzer.document_engine import DocumentEngine
from core.stock_market.market_engine import MarketEngine
from logger import llm_logger as logger

async def finacial_agent(query: str, chat_id: str) -> str:
    """
    This function retrieves relevant information from the vector database based on the user's query.
    Both from the Document VectorDB and the Financial Stock Market VectorDB.
    Args:
        query (str): The user's query to search for relevant information.
    Returns:
        str: The relevant information retrieved from the vector database based on user query.
    """

    document_query_result = "No relevant documents found."
    financial_query_result = "No relevant financial data found."

    try:
        # Initialize the Document Engine
        document_engine = DocumentEngine(chat_id=chat_id)
        doc_results = document_engine.query_documents(query=query, k=5)
        if doc_results:
            document_query_result = "\n".join([doc.text for doc in doc_results])
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")

    try:
        # Initialize the Financial Document Engine
        market_engine = MarketEngine()
        market_results = market_engine.query_market_data(query=query, k=5)
        if market_results:
            financial_query_result = "\n".join([doc.page_content for doc in market_results])
    except Exception as e:
        logger.error(f"Error querying financial market data: {str(e)}")

    # Combine results from both engines
    combined_results = f"# Financial Market Data Results:\n{financial_query_result}\n\n# Finacial Document Results:\n{document_query_result}"
    #logger.debug(f"Combined results for query '{query}': {combined_results}")
    return combined_results

function_definations = {
    "finacial_agent": finacial_agent
}