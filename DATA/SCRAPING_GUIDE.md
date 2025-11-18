# How to Scrape Reddit Data for TrustMed AI

This guide walks you through the steps to scrape Reddit discussion threads about Type II Diabetes and Heart Disease/Hypertension **without requiring Reddit API credentials**.

## Prerequisites

1. **Python 3.7+** installed
2. **No Reddit account or API credentials needed!**

## Step 1: Install Dependencies

From the project root directory, install required packages:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install praw pandas python-dotenv requests beautifulsoup4
```

## Step 2: Run the Scraper

You have **three scraping methods** available (no API credentials needed):

### Method 1: Public JSON API (Recommended - Fastest)

This method uses Reddit's public JSON endpoints by appending `.json` to URLs. **No authentication required!**

```bash
python3 data_collection/scripts/collect_reddit_public.py
```

**Pros:**
- Fast and efficient
- No API credentials needed
- Gets structured JSON data
- Works for most cases

**Cons:**
- May occasionally get rate limited (script handles this automatically)

### Method 2: HTML Web Scraping

This method scrapes Reddit HTML pages directly using BeautifulSoup:

```bash
python3 data_collection/scripts/scrape_reddit_html.py
```

**Pros:**
- No API or JSON endpoints needed
- More resilient to API changes
- Works even if JSON endpoints are blocked

**Cons:**
- Slower than JSON method
- More complex parsing
- May need updates if Reddit changes HTML structure

### Method 3: Using PRAW with API (Requires Credentials)

Only use this if Methods 1 and 2 don't work. Requires creating a Reddit app:

```bash
# First set up credentials (see troubleshooting section)
python3 data_collection/scripts/collect_with_praw.py
```

## Step 3: Monitor Progress

The script will:
- Display progress as it collects threads
- Show which subreddits it's accessing
- Print the number of threads collected
- Save data automatically when complete

Example output:
```
======================================================================
TrustMed AI - Health Forum Data Collection with PRAW
======================================================================

Start time: 2025-01-15 10:30:00

✓ Reddit API connection established
✓ Authenticated as: TrustMedAI Health Forum Collector v1.0

======================================================================
Collecting threads for: DIABETES
Target: 500 threads
======================================================================

Collecting from r/diabetes...
  - Fetching hot posts...
    Added 45 relevant threads (total: 45)
  - Fetching top (month) posts...
    Added 32 relevant threads (total: 77)
  ...
```

## Step 4: Check Your Data

After collection completes, your data will be saved in:
- **JSON files**: `data_collection/data/diabetes_threads_YYYYMMDD_HHMMSS.json`
- **CSV files**: `data_collection/data/diabetes_threads_YYYYMMDD_HHMMSS.csv`

View the files:
```bash
# List collected files
ls -lh data_collection/data/

# View CSV summary (first 20 lines)
head -20 data_collection/data/diabetes_threads_*.csv

# Count total threads
wc -l data_collection/data/*_threads_*.csv
```

## What Gets Collected

For each thread, the script collects:
- **Post information**: Title, author, subreddit, creation date, score, URL
- **Post content**: Full text of the original post
- **Comments**: Top 20-30 comments with author, body, score, and timestamp
- **Metadata**: Upvote ratio, number of comments, collection timestamp

## Target Subreddits

### Type II Diabetes:
- r/diabetes
- r/diabetes_t2
- r/type2diabetes

### Heart Disease/Hypertension:
- r/hypertension
- r/HeartDisease

## Troubleshooting

### Error: "Reddit API credentials not found!"
**Solution**: This only applies if using Method 3 (PRAW). Use Method 1 or 2 instead - they don't require credentials!

### Error: "403 Forbidden" or "Rate limited"
**Solution**: 
- Reddit may be blocking requests. Wait a few minutes and try again.
- Use Method 1 (PRAW) instead of public API.
- The script includes rate limiting (1-2 second delays between requests).

### Error: "Cannot access r/subreddit"
**Solution**: 
- Check that the subreddit name is correct.
- Some subreddits may be private or restricted.
- Verify your Reddit API credentials are correct.

### Not collecting enough threads
**Solution**:
- The script filters threads by keywords. You may need to adjust keywords in the script.
- Try collecting from more subreddits.
- Increase the `limit_per_source` parameter in the script.

### Script runs but collects 0 threads
**Solution**:
- Check that the keyword filters aren't too restrictive.
- Verify the subreddits exist and are accessible.
- Try running with verbose output to see what's happening.

## Expected Collection Time

- **500 threads per disease area**: ~30-60 minutes
- **1000 total threads**: ~1-2 hours

The script includes rate limiting to respect Reddit's API limits, so it may take some time.

## Data Format

### JSON Structure
Each thread is saved as a JSON object with:
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
  "collected_at": "2025-01-20T15:00:00"
}
```

### CSV Structure
The CSV contains a summary with columns:
- id, title, author, subreddit, created_utc
- score, num_comments, url, selftext (truncated)
- upvote_ratio, num_collected_comments

## Next Steps

After collecting data:
1. Review the collected threads for quality
2. Clean and filter the data as needed
3. Proceed with your analysis (KRT extraction, theme identification, etc.)

## Important Notes

- **Respect Reddit's Terms of Service**: Only collect publicly available data
- **Rate Limiting**: The script includes delays to avoid overwhelming Reddit's servers
- **Privacy**: Be mindful of user privacy when using collected data
- **Research Ethics**: Follow your institution's IRB guidelines for human subjects research

## Support

For issues:
1. Check the main README.md in `data_collection/`
2. Review Reddit API documentation: https://www.reddit.com/dev/api/
3. Check PRAW documentation: https://praw.readthedocs.io/

