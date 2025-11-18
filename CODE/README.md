# CODE

This directory contains all the source code for the TrustMed AI project.

## Structure

### `app/`
The main Chainlit-based web application for the TrustMed AI chatbot.

- **app.py** - Main application file with RAG pipeline, LangChain integration, and Chainlit UI
- **public/** - Frontend assets (CSS themes, banners, images)
- **scripts/** - Utility scripts (e.g., sync_kb.py for knowledge base synchronization)
- **requirements.txt** - Python dependencies for the application
- **chainlit.md** - Welcome message and instructions for the chat interface

### `data_collection_scripts/`
Python scripts for collecting and processing data from various sources.

- **scrape_medical_articles.py** - Scrapes authoritative medical content from Mayo Clinic, CDC, etc.
- **collect_reddit_threads.py** - Collects patient discussions from Reddit
- **scrape_focused.py** - Focused scraping for specific medical topics
- **prepare_upload.py** - Prepares collected data for upload to S3
- **upload_to_s3.py** - Uploads processed data to Amazon S3
- **combine_files.py** - Combines multiple data files
- **medical_article_urls.py** - URLs for medical article sources
- And other collection/processing utilities

## Requirements

See individual `requirements.txt` files in subdirectories or the root-level file for dependencies.

## Setup

### Environment Configuration

**Important:** Before running the application, you must configure environment variables.

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your AWS credentials and configuration:
   ```bash
   nano .env
   ```

3. Required variables:
   - `AWS_REGION` - Your AWS region (e.g., `us-east-1`)
   - `BEDROCK_KB_ID` - Your Bedrock Knowledge Base ID
   - `BEDROCK_MODEL_ARN` - Model ARN (e.g., `meta.llama3-8b-instruct-v1:0`)

See `SETUP.md` for detailed configuration instructions.

## Usage

### Running the Application
```bash
cd app
pip install -r requirements.txt

# Make sure .env is configured first!
chainlit run app.py
```

### Data Collection
```bash
cd data_collection_scripts
# Configure your credentials in config_template.py
python scrape_medical_articles.py
python collect_reddit_threads.py
python prepare_upload.py
python upload_to_s3.py
```

