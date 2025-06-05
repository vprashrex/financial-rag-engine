"""
Script to test the LLM RAG Agent functionality.
"""

import asyncio
from core.llm_rag_agent.llm import GenaiChat

async def main():
    """
    Main function to test the LLM RAG Agent functionality.
    """
    chat_id = "1749144027284"  # Contains Walmart 2025 Annual Report.pdf

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
Query: "Hello"
Output: Hello! How can I assist you today?

** Note ** -> Didn't run agent RAG tool

-------------- EXAMPLE 2 ----------------------------
Query: "What is the current stock price of Apple?"
Output: The stock price of Apple (AAPL) is $202.82, with a daily change of -0.04%. This data was last updated on 2025-06-04.

** Note ** -> Run agent RAG tool

-------------- EXAMPLE 3 ----------------------------
Query: "Can you provide the technical analysis for Apple?"
Output: Here's the technical analysis for Apple (AAPL) based on the latest financial market data (as of 2025-06-04):

*   **Price:** $202.82
*   **Volume:** 43,603,985
*   **Daily Change:** -0.04%

**Technical Indicators:**
*   **MA(5) (5-day Moving Average):** $201.72
*   **MA(20) (20-day Moving Average):** $203.73
*   **RSI (Relative Strength Index):** 32.0
*   **Volatility:** 29.5%
*   **ATR (Average True Range):** $4.43

** Note ** -> Run agent RAG tool

# -------------- EXAMPLE 4 -----------------------------
Query: "What are the current prices of Bitcoin and Ethereum?"
Output: Based on the financial market data, the current prices are:

*   **Ethereum (ETH-USD):** $2614.57 (Last Update: 2025-06-05)
*   **Bitcoin (BTC-USD):** $104896.58 (Last Update: 2025-06-05)

** Note ** -> Run agent RAG tool

# -------------- EXAMPLE 5 -----------------------------
Query: "What is MCP Server in context of GenAI?"
Output: I am sorry, but I do not have enough information to answer your question about "MCP Server in the context of GenAI". My knowledge base does not contain specific details about this term.

** Note ** -> Didn't run agent RAG tool

# -------------- EXAMPLE 6 -----------------------------
Query: what is the total liabilites of wallmart?
Output: As of January 31, 2025, Walmart's total liabilities can be calculated using the accounting equation: Total Assets = Total Liabilities + Total Shareholders' Equity.

Based on the provided financial document results:
*   **Total Assets** as of January 31, 2025: $260,823 million
*   **Total Shareholders' Equity** as of January 31, 2025: $97,421 million

Therefore, the **Total Liabilities** are calculated as:
$260,823 million (Total Assets) - $97,421 million (Total Shareholders' Equity) = **$163,402 million**.

** Note ** -> Run agent RAG tool

# -------------- EXAMPLE 7 -----------------------------
Query: Provide in single line
Output: Walmart's total liabilities as of January 31, 2025, are $163,402 million.

** Note ** -> Didn't run agent RAG tool
"""

if __name__ == '__main__':
    asyncio.run(main())