# 🩺 TrustMed AI  
**An AI-powered chatbot that bridges medical expertise with real-world patient experience.**

---

## 🧠 Overview  
**TrustMed AI** helps patients find clear, reliable information about **Diabetes** and **Cardiovascular Disease**.  
It combines **authoritative medical content** (Mayo Clinic, CDC, MedlinePlus) with **patient discussions** from Reddit to deliver answers that are **accurate, empathetic, and cited**.  
Built as a **Retrieval-Augmented Generation (RAG)** system, it grounds every response in verifiable evidence.

---

## ⚙️ Architecture  
- **Data Sources:**  
  - Clinical articles → validated medical facts  
  - Reddit threads → real-world questions and language  
- **Processing Pipeline:**  
  - Python scripts scrape and clean data (`Requests`, `BeautifulSoup`, `Pandas`)  
  - Metadata and citations added → uploaded to **Amazon S3**  
- **Knowledge Base:**  
  - **Embeddings:** Amazon Titan Text v2  
  - **Vector DB:** Amazon OpenSearch (k-NN + BM25 hybrid search)  
  - **LLM:** Meta Llama 3 8B Instruct via AWS Bedrock  
- **Frontend:** [Chainlit](https://docs.chainlit.io) chat UI with streaming answers and clickable citations  
- **Evaluation:** [TruLens](https://www.trulens.org) for Answer Relevance, Context Relevance & Groundedness  

---

## 🧩 Tech Stack
**Python · LangChain · Chainlit · AWS EC2 · S3 · OpenSearch · Bedrock · TruLens**

---

## 📈 Highlights  
✅ Dual-source dataset (clinical + patient)  
✅ Hybrid semantic + keyword retrieval  
✅ Transparent citations for trustworthy answers  
✅ Evaluated with TruLens for quality and grounding  

---

**Team 3 — FA25 Group Project**  
Shitij Mathur · Advaith Venkatsubramanian · Suhas Gajula · Thanishka Bolisetty · Varad More · Vishnu Menon  
