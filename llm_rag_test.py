"""
Script to test the LLM RAG (Retrieval-Augmented Generation) functionality.
"""
import asyncio
from core.llm_rag.llm import GenaiChat

async def main():
    """
    Main function to test the LLM RAG functionality.
    """
    chat_id = "test_chat_id" # use 1234 chat_id for testing finacial document retrieval

    # Initialize the GenaiChat instance
    genai_chat = GenaiChat()

    while True:
        user_query = input("Enter your query (or 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break

        # Generate user content
        response = await genai_chat.generate(user_query, chat_id)
        
        # Print the generated user content
        print("Generated User response:")
        print(response)

"""
Example Query and Output:
--------------- EXAMPLE 1 ----------------------------
Query: "What is the current stock price of Apple?"
Output: The current stock price of Apple Inc. (AAPL) is $202.82.

-------------- EXAMPLE 2 ----------------------------
Query: "Can you provide the technical analysis for Apple?"
Output: Here is the technical analysis for Apple (AAPL):

**Technical Indicators:**
*   **MA(5):** $201.72
*   **MA(20):** $203.73
*   **RSI:** 32.0
*   **Volatility:** 29.5%
*   **ATR:** $4.43

*Last Update: 2025-06-04*

-------------- EXAMPLE 3 -----------------------------
Query: "What are the current price of bitcoin and ethereum?"
Output: The current price of Bitcoin (BTC-USD) is $104896.58 and Ethereum (ETH-USD) is $2614.57.

"""

if __name__ == '__main__':
    asyncio.run(main())