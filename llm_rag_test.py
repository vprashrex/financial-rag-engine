"""
Script to test the LLM RAG (Retrieval-Augmented Generation) functionality.
"""
import asyncio
from core.llm_rag.llm import GenaiChat

async def main():
    """
    Main function to test the LLM RAG functionality.
    """
    chat_id = "1749144432787"  # This chat_id uses Amazon 2024 Anual Report as the finacial document.

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

-------------- EXAMPLE 4 -----------------------------
Query: "What is the acquisition activity of the company?"
Output: Based on the financial documents, the company's acquisition activity for recent years is as follows:

*   **2024:** Aggregate cash consideration of $780 million, net of cash acquired. The primary reasons were to acquire technologies and know-how to serve customers more effectively or expand the customer base.
*   **2023:**
    *   Acquired 1Life Healthcare, Inc. (One Medical) for approximately $3.5 billion in cash, net of cash acquired, to provide healthcare options for customers.   
    *   Also completed acquisition activity for immaterial aggregate cash consideration, net of cash acquired.
*   **2022:**
    *   Acquired MGM Holdings Inc. for approximately $6.1 billion in cash, net of cash acquired, to provide more digital media content options for customers.      
    *   Also completed acquisition activity for aggregate cash consideration of $141 million, net of cash acquired.

---------------- EXAMPLE 5 -----------------------------
Query: provide detailed anlaysis of the cash flow of the company
Output: Based on the financial documents, here is a detailed analysis of the company's cash flow related items:

**Consolidated Statements of Cash Flows Reconciliation:**

*   **Total cash, cash equivalents, and restricted cash shown in the consolidated statements of cash flows:**
    *   $73,890 million
    *   $82,312 million

**Components of Restricted Cash:**

*   Restricted cash included in accounts receivable, net and other: $497 million and $247 million.
*   Restricted cash included in other assets: $6 million and $3,286 million.

This reconciliation provides insight into how cash, cash equivalents, and restricted cash are reported and reconciled within the consolidated financial statements.

----------------- EXAMPLE 6 -----------------------------
Query: what is the total debt of the company in year 2024?
Output: Based on the financial documents, the company's total debt for the year 2024 can be detailed by summing its various components:

*   **Unsecured Senior Notes Outstanding:** $58.0 billion as of December 31, 2024.
*   **Total Long-Term Debt Obligations (based on future principal payments schedule):** $7,439 million (or approximately $7.44 billion) as of December 31, 2024. This figure represents the sum of scheduled principal payments for what the document refers to as "our total long-term debt."
*   **Long-term Financing Obligations:** $7.1 billion as of December 31, 2024, included in "Other long-term liabilities."
*   **Current Financing Obligations:** $312 million (or approximately $0.31 billion) as of December 31, 2024, included in "Accrued expenses and other."
*   **Borrowings outstanding under other short-term credit facilities:** $151 million (or approximately $0.15 billion) as of December 31, 2024, included in "Accrued expenses and other."

**Total Debt Calculation for 2024:**

To arrive at a comprehensive total debt figure, we sum these distinct components:
$58,000 million (Unsecured Senior Notes)
+ $7,439 million (Total Long-Term Debt Obligations from schedule)
+ $7,100 million (Long-term Financing Obligations)
+ $312 million (Current Financing Obligations)
+ $151 million (Other Short-term Credit Facilities)
= **$73,002 million** or approximately **$73.00 billion**.

**Note on Long-Term Debt Figures:**
The financial document states $58.0 billion for "unsecured senior notes outstanding" and separately presents a table of "future principal payments for our total long-term debt" that sums to $7,439 million. While the phrasing "total long-term debt" for the latter suggests it encompasses all long-term debt, the significant difference in magnitude from the $58.0 billion senior notes indicates that these are likely distinct categories or that the $7,439 million table represents only the scheduled maturities for a portion of the long-term debt, not the entire outstanding principal of all long-term debt if certain notes (like the $58.0 billion) have much longer maturities. For this calculation, both the outstanding senior notes and the separate long-term debt obligations from the maturity schedule are included as distinct components.

------------ EXAMPLE 7 -----------------------------
Query: provide it in small brief
Output: In 2024, the company's total debt is approximately **$73.00 billion**. This includes **$58.0 billion in unsecured senior notes**, along with other long-term debt obligations, long-term and current financing obligations, and short-term credit facilities.
"""

if __name__ == '__main__':
    asyncio.run(main())