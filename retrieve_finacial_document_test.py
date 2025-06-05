"""
This script is used to test the embedding and querying of financial documents.
"""

from core.document_analyzer.document_engine import DocumentEngine

def embedding_financial_document():
    """
    This function is used to parse and store a financial document in the vector database.
    It simulates the process of uploading a financial document, parsing it, and storing the parsed content in the vector database.
    """
    document_path = "uploads/1234/FY25_Q2_Consolidated_Financial_Statements.pdf"
    chat_id = "1234"
    document_engine = DocumentEngine(chat_id=chat_id)
    result = None
    try:
        result = document_engine.process_and_store_pdf(file_path=document_path)
        print(f"Document {document_path} successfully parsed and stored.")
    except Exception as e:
        print(f"Error processing document {document_path}: {str(e)}")

    print("Document embedding completed successfully.")
    print("Result:\n\n", result)


def query_from_finacial_document():
    """
    This function is used to query a financial document stored in the vector database.
    """
    # uploads\1234\FY25_Q2_Consolidated_Financial_Statements.pdf
    chat_id = "1234"
    query = "net sales of apple inc in march 29 2025"
    document_engine = DocumentEngine(chat_id=chat_id)
    doc_results = document_engine.query_documents(query=query, k=1)
    if doc_results:
        for doc in doc_results:
            print("----------------------------------")
            print(f"Document ID: {doc.id}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content: {doc.page_content}\n")
    else:
        print("No relevant documents found.")

    """
    --------------------------------------------------------------
    query = "net sales of apple inc in march 29 2025"
    k = 1  # Number of results to return
    --------------------------------------------------------------
    Output:
    Content: # Apple Inc.
    # CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Unaudited)

    # (In millions)

    |                                                                                      | Six Months Ended | March 29, 2025 | March 30, 2024 |
    | ------------------------------------------------------------------------------------ | ---------------- | -------------- | -------------- |
    | Cash, cash equivalents, and restricted cash and cash equivalents, beginning balances |                  | $ 29,943       | $ 30,737       |

    # Operating activities:
    """

if __name__ == "__main__":

    # Uncomment the line below to embed a financial document
    # embedding_financial_document()

    # query from financial document
    query_from_finacial_document()