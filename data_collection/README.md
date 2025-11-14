# TrustMed AI - Health Forum Data Collection

This directory contains scripts and tools for collecting discussion threads from online health forums and patient communities, focusing on Type II Diabetes and Heart Disease/Hypertension.

## Project Goal

Collect 500-1,000 discussion threads from relevant online health forums to identify Key Recurring Themes (KRTs) related to:
- Symptoms and early warning signs
- Medications, dosages, and side effects
- Treatments and management strategies
- Lifestyle adjustments

## Directory Structure

```
data_collection/
├── scripts/           # Data collection scripts
│   ├── collect_with_praw.py          # Reddit collector using PRAW (requires API credentials)
│   ├── collect_reddit_public.py      # Reddit collector using public API (no auth)
│   ├── collect_reddit_threads.py     # Original PRAW-based collector
│   └── config_template.py            # Configuration template
├── data/              # Collected data (JSON and CSV files)
├── logs/              # Collection logs
└── README.md          # This file
```

## Data Collection Methods

### Method 1: Reddit API with PRAW (Recommended)

This method uses Reddit's official API through the PRAW (Python Reddit API Wrapper) library.

**Prerequisites:**
1. A Reddit account
2. Reddit API credentials (client_id and client_secret)

**Setup Steps:**

1. **Get Reddit API Credentials:**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Fill in:
     - **Name:** TrustMed AI Data Collector
     - **App type:** script
     - **Description:** Health forum data collection for academic research
     - **About URL:** (leave blank)
     - **Redirect URI:** http://localhost:8080
   - Click "Create app"
   - Note your **client_id** (under the app name) and **client_secret**

2. **Configure Credentials:**

   Option A - Environment Variables (Recommended):
   ```bash
   export REDDIT_CLIENT_ID='your_client_id_here'
   export REDDIT_CLIENT_SECRET='your_client_secret_here'
   ```

   Option B - Create config.py:
   ```bash
   cd data_collection/scripts/
   cp config_template.py config.py
   # Edit config.py and add your credentials
   ```

3. **Run the Collector:**
   ```bash
   python3 data_collection/scripts/collect_with_praw.py
   ```

**Target Subreddits:**
- Type II Diabetes: r/diabetes, r/diabetes_t2, r/type2diabetes
- Heart Disease: r/hypertension, r/HeartDisease

### Method 2: Public API (No Authentication)

This method attempts to use Reddit's public JSON endpoints. However, Reddit has implemented stricter access controls, and this method may not work consistently.

```bash
python3 data_collection/scripts/collect_reddit_public.py
```

**Note:** This method is less reliable due to Reddit's anti-bot measures.

### Method 3: Manual Collection

If automated methods don't work, you can manually collect data:

1. **Reddit:**
   - Visit target subreddits
   - Search for relevant keywords
   - Manually save discussion threads

2. **Alternative Forums:**
   - **Diabetes Forums:**
     - TuDiabetes.org
     - DiabetesDaily.com
     - r/diabetes (Reddit)

   - **Heart Disease Forums:**
     - Heart Support Community
     - MyHeartDiseaseTeam.com
     - r/hypertension (Reddit)

## Data Format

### JSON Format (Full Data)
```json
{
  "id": "post_id",
  "title": "Discussion title",
  "author": "username",
  "subreddit": "diabetes",
  "created_utc": "2024-01-15T10:30:00",
  "score": 125,
  "num_comments": 45,
  "url": "https://reddit.com/r/diabetes/...",
  "selftext": "Full post content...",
  "upvote_ratio": 0.95,
  "comments": [
    {
      "author": "commenter",
      "body": "Comment text...",
      "score": 10,
      "created_utc": "2024-01-15T11:00:00"
    }
  ],
  "collected_at": "2024-01-20T15:00:00"
}
```

### CSV Format (Summary)
- id
- title
- author
- subreddit
- created_utc
- score
- num_comments
- url
- selftext (truncated)
- upvote_ratio
- num_collected_comments

## Usage Examples

### Collect with Default Settings
```bash
python3 data_collection/scripts/collect_with_praw.py
```

### Check Collected Data
```bash
# List collected files
ls -lh data_collection/data/

# View CSV summary
head -20 data_collection/data/diabetes_threads_*.csv

# Count total threads
wc -l data_collection/data/*_threads_*.csv
```

### Load Data in Python
```python
import json
import pandas as pd

# Load JSON data
with open('data_collection/data/diabetes_threads_20240120_150000.json', 'r') as f:
    threads = json.load(f)

# Load CSV data
df = pd.read_csv('data_collection/data/diabetes_threads_20240120_150000.csv')

print(f"Total threads: {len(threads)}")
print(f"Average score: {df['score'].mean()}")
print(f"Total comments: {df['num_comments'].sum()}")
```

## Troubleshooting

### Issue: "403 Forbidden" errors
**Solution:**
- Use Method 1 with proper Reddit API credentials
- Reddit blocks direct scraping; API access is required

### Issue: "Rate limited" errors
**Solution:**
- The scripts include rate limiting (2-5 second delays)
- If rate limiting persists, increase delays in the script
- Consider collecting data in smaller batches

### Issue: Not enough threads collected
**Solution:**
- Expand search to more subreddits
- Include related terms in keyword lists
- Collect over longer time periods
- Consider alternative health forums

### Issue: API credentials not working
**Solution:**
- Verify credentials are correct
- Ensure app type is set to "script"
- Check redirect URI is http://localhost:8080
- Regenerate credentials if needed

## Data Quality Guidelines

When collecting threads, prioritize:
1. **Relevance:** Threads discussing symptoms, medications, or management
2. **Engagement:** Posts with multiple comments (5+)
3. **Recency:** Posts from the last 1-2 years
4. **Quality:** Well-written posts with detailed information
5. **Diversity:** Mix of questions, experiences, and advice

## Privacy and Ethics

- Only collect publicly available data
- Do not collect private messages or restricted content
- Remove or anonymize personally identifiable information
- Use data only for research and educational purposes
- Respect Reddit's API Terms of Service
- Follow your institution's IRB guidelines for human subjects research

## Next Steps

After collecting 500-1,000 threads:

1. **Data Cleaning:**
   - Remove duplicates
   - Filter spam and irrelevant posts
   - Standardize formatting

2. **Qualitative Analysis:**
   - Identify Key Recurring Themes (KRTs)
   - Categorize discussions by theme
   - Extract common patterns

3. **Theme Extraction:**
   - Symptoms and warning signs
   - Medication experiences
   - Treatment strategies
   - Lifestyle modifications

## Support

For issues or questions:
1. Check Reddit API documentation: https://www.reddit.com/dev/api/
2. PRAW documentation: https://praw.readthedocs.io/
3. Review error logs in `data_collection/logs/`

## License

This project is for educational and research purposes. Respect all applicable terms of service and data use policies.
