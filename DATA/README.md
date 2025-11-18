# DATA

This directory contains all data collected and processed for the TrustMed AI knowledge base.

## Structure

### `processed/`
Cleaned and formatted data ready for upload to the knowledge base.

#### `processed/authoritative/`
Medical content from authoritative sources:
- **cdc/** - Centers for Disease Control and Prevention articles
- **healthline/** - Healthline medical articles
- **johns-hopkins-medicine/** - Johns Hopkins Medicine content
- **mayo-clinic/** - Mayo Clinic articles (comprehensive diabetes and cardiovascular content)
- **medical-xpress/** - Medical Xpress research news
- **medicalnewstoday/** - Medical News Today articles
- **medlineplus/** - MedlinePlus health information
- **webmd/** - WebMD medical content
- **who/** - World Health Organization resources

#### `processed/forums/`
Patient discussions and community content from Reddit:
- **askcardiology/** - Q&A from r/AskCardiology
- **cardiology/** - Discussions from r/cardiology
- **diabetes/** - Content from r/diabetes
- **diabetes-t2/** - Type 2 diabetes discussions
- **heartdisease/** - Heart disease community posts
- **hypertension/** - Hypertension-related discussions
- **prediabetes/** - Prediabetes community content
- **type2diabetes/** - Type 2 diabetes discussions

#### `manifest.json`
Metadata file describing all processed data files, including source URLs, titles, and document IDs.

### `raw_collected/`
Raw data as collected from sources before processing.

#### `raw_collected/auth_src/`
- **medical_articles/** - Original scraped medical articles with metadata

#### `raw_collected/forum_src/`
- CSV and JSON files of collected Reddit threads

#### `raw_collected/backup/`
- Backup copies of collected data with timestamps

## Data Summary

- **~200 authoritative medical articles** covering diabetes and cardiovascular disease
- **~1,500 forum posts** from Reddit medical communities
- Total data size: Several MB of text content

## Documentation

- **DATA_SUMMARY.md** - Detailed overview of data sources and statistics
- **SCRAPING_GUIDE.md** - Instructions for data collection
- **README.md** - This file

## Notes

- All data is stored as plain text (.txt) files for easy processing
- Each file includes source attribution and metadata
- Data is organized by source type (authoritative vs. forums) and topic
- The processed data is ready for embedding and vector database upload
