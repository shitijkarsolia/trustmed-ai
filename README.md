# 🩺 TrustMed AI  
**An AI-powered chatbot that bridges medical expertise with real-world patient experience.**

---

## 🧠 Overview  
**TrustMed AI** helps patients find clear, reliable information about **Diabetes** and **Cardiovascular Disease**.  
It combines **authoritative medical content** (Mayo Clinic, CDC, MedlinePlus) with **patient discussions** from Reddit to deliver answers that are **accurate, empathetic, and cited**.  
Built as a **Retrieval-Augmented Generation (RAG)** system, it grounds every response in verifiable evidence.

---

## 📁 Repository Structure

```
trustmed-ai/
├── CODE/                    # All source code
│   ├── app/                # Main Chainlit application
│   └── data_collection_scripts/  # Data scraping and processing scripts
├── DATA/                    # All data files
│   ├── processed/          # Cleaned data ready for KB upload
│   │   ├── authoritative/  # Medical articles from trusted sources
│   │   └── forums/         # Reddit community discussions
│   └── raw_collected/      # Original scraped data
├── EVALUATIONS/            # TruLens evaluation scripts and results
├── REFERENCE/              # Project documentation and references
└── README.md               # This file
```

Each directory contains its own README with detailed information.

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

## 🚀 Quick Start

### 1. Environment Setup

**Configure your environment variables first:**

```bash
# Copy the template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required variables:
- `AWS_REGION` - Your AWS region
- `BEDROCK_KB_ID` - Your Bedrock Knowledge Base ID  
- `BEDROCK_MODEL_ARN` - Model to use (e.g., `meta.llama3-8b-instruct-v1:0`)

See `CODE/SETUP.md` for detailed instructions.

### 2. Running the Application
```bash
cd CODE/app
pip install -r requirements.txt
chainlit run app.py
```

### Data Collection
```bash
cd CODE/data_collection_scripts
python scrape_medical_articles.py
python collect_reddit_threads.py
python prepare_upload.py
```

### Evaluations
```bash
cd EVALUATIONS
python evaluations.py
```

---

## 📈 Highlights  
✅ Dual-source dataset (clinical + patient)  
✅ Hybrid semantic + keyword retrieval  
✅ Transparent citations for trustworthy answers  
✅ Evaluated with TruLens for quality and grounding  

---

**Team 3 — FA25 Group Project**  
Shitij Mathur · Advaith Venkatsubramanian · Suhas Gajula · Thanishka Bolisetty · Varad More · Vishnu Menon  
