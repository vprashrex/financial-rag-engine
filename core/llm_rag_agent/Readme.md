# 🧠 LLM RAG AGENT

This module ensures **agentic Retrieval-Augmented Generation (RAG)**, where all interactions with the LLM are mediated through an agent-based tool. The agent handles context retrieval from the VectorDB and dynamically routes relevant context to the LLM, enabling grounded and context-aware responses.

---

## 🚀 Features

* 🔍 **Agentic Context Retrieval**
  The agent fetches relevant documents from the VectorDB based on the query intent.

* 🧩 **LLM Abstraction via Tool Use**
  The LLM is not directly queried. Instead, an agent tool handles request orchestration, grounding the query with external context.

* 🧠 **Decoupled Intelligence**
  Clean separation between vector search logic and language generation.

* 🧱 **Composable and Extendable**
  Modular architecture allows plugging in various VectorDBs (e.g., FAISS, Weaviate) and LLMs (e.g., OpenAI, Cohere).

---

## To test this feature use the below command
```
python llm_rag_agent_test.py
```