#!/usr/bin/env python3
"""
Reddit Health Forum Data Collection Script using PRAW
Requires Reddit API credentials.

Setup Instructions:
1. Create a Reddit account if you don't have one
2. Go to https://www.reddit.com/prefs/apps
3. Click "Create App" or "Create Another App"
4. Fill in:
   - Name: TrustMed AI Data Collector
   - App type: script
   - Description: Health forum data collection for research
   - Redirect URI: http://localhost:8080
5. Save the client_id and client_secret
6. Set them as environment variables or create config.py
"""

import praw
import pandas as pd
import json
import time
from datetime import datetime
import os
import sys

# Try to import config
try:
    from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
except ImportError:
    # Try environment variables
    REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', '')
    REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', '')
    REDDIT_USER_AGENT = 'TrustMedAI Health Forum Collector v1.0'

# Configuration
DISEASE_AREAS = {
    'diabetes': {
        'subreddits': ['diabetes', 'diabetes_t2', 'type2diabetes'],
        'keywords': ['type 2', 't2', 'type ii', 'diabetes', 'blood sugar', 'glucose',
                     'insulin resistance', 'metformin', 'hba1c', 'prediabetes'],
        'target_count': 500
    },
    'heart_disease': {
        'subreddits': ['hypertension', 'HeartDisease'],
        'keywords': ['heart disease', 'hypertension', 'high blood pressure', 'cardiovascular',
                     'cholesterol', 'bp', 'blood pressure', 'heart attack', 'cardiac'],
        'target_count': 500
    }
}

OUTPUT_DIR = '/home/user/trustmed-ai/data_collection/data'

class RedditCollector:
    """Collects health-related discussion threads from Reddit using PRAW."""

    def __init__(self, client_id, client_secret, user_agent):
        """Initialize Reddit API connection."""
        if not client_id or not client_secret:
            print("ERROR: Reddit API credentials not found!")
            print("\nPlease set up credentials by either:")
            print("1. Creating config.py with REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            print("2. Setting environment variables:")
            print("   export REDDIT_CLIENT_ID='your_client_id'")
            print("   export REDDIT_CLIENT_SECRET='your_client_secret'")
            print("\nTo get credentials, visit: https://www.reddit.com/prefs/apps")
            sys.exit(1)

        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.reddit.read_only = True
            print("✓ Reddit API connection established")
            print(f"✓ Authenticated as: {user_agent}")
        except Exception as e:
            print(f"✗ Error connecting to Reddit API: {e}")
            sys.exit(1)

    def collect_threads(self, disease_area, limit_per_source=200):
        """Collect threads for a specific disease area."""
        threads = []
        seen_ids = set()

        for subreddit_name in disease_area['subreddits']:
            print(f"\nCollecting from r/{subreddit_name}...")

            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Verify subreddit is accessible
                try:
                    _ = subreddit.display_name
                except Exception as e:
                    print(f"  ✗ Cannot access r/{subreddit_name}: {e}")
                    continue

                # Collect from different sorting methods
                for sort_method, sort_label in [
                    (lambda: subreddit.hot(limit=limit_per_source), 'hot'),
                    (lambda: subreddit.top(time_filter='month', limit=limit_per_source), 'top (month)'),
                    (lambda: subreddit.new(limit=limit_per_source), 'new')
                ]:
                    print(f"  - Fetching {sort_label} posts...")

                    try:
                        posts = sort_method()
                        count = 0

                        for post in posts:
                            if post.id in seen_ids:
                                continue

                            # Check if post is relevant
                            if self._is_relevant(post, disease_area['keywords']):
                                thread_data = self._extract_thread_data(post)
                                if thread_data:
                                    threads.append(thread_data)
                                    seen_ids.add(post.id)
                                    count += 1

                            # Rate limiting
                            if count % 10 == 0:
                                time.sleep(1)

                        print(f"    Added {count} relevant threads (total: {len(threads)})")

                    except Exception as e:
                        print(f"    ✗ Error fetching {sort_label} posts: {e}")

            except Exception as e:
                print(f"  ✗ Error with r/{subreddit_name}: {e}")
                continue

        return threads

    def _is_relevant(self, post, keywords):
        """Check if a post is relevant based on keywords."""
        text = f"{post.title} {post.selftext}".lower()
        return any(keyword.lower() in text for keyword in keywords)

    def _extract_thread_data(self, post):
        """Extract relevant data from a Reddit post."""
        try:
            # Get comments (limit to avoid timeout)
            post.comments.replace_more(limit=3)
            comments = []

            for comment in post.comments.list()[:30]:
                if hasattr(comment, 'body') and comment.body:
                    comments.append({
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat()
                    })

            thread_data = {
                'id': post.id,
                'title': post.title,
                'author': str(post.author) if post.author else '[deleted]',
                'subreddit': str(post.subreddit),
                'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                'score': post.score,
                'num_comments': post.num_comments,
                'url': f"https://reddit.com{post.permalink}",
                'selftext': post.selftext,
                'upvote_ratio': post.upvote_ratio,
                'comments': comments,
                'collected_at': datetime.now().isoformat()
            }

            return thread_data

        except Exception as e:
            print(f"    ✗ Error extracting thread data: {e}")
            return None

    def save_data(self, threads, disease_name):
        """Save collected threads to JSON and CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save as JSON
        json_filename = f"{OUTPUT_DIR}/{disease_name}_threads_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved full data to: {json_filename}")

        # Save as CSV
        csv_data = []
        for thread in threads:
            csv_row = {
                'id': thread['id'],
                'title': thread['title'],
                'author': thread['author'],
                'subreddit': thread['subreddit'],
                'created_utc': thread['created_utc'],
                'score': thread['score'],
                'num_comments': thread['num_comments'],
                'url': thread['url'],
                'selftext': thread['selftext'][:500] if thread['selftext'] else '',
                'upvote_ratio': thread['upvote_ratio'],
                'num_collected_comments': len(thread['comments'])
            }
            csv_data.append(csv_row)

        df = pd.DataFrame(csv_data)
        csv_filename = f"{OUTPUT_DIR}/{disease_name}_threads_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"✓ Saved summary to: {csv_filename}")

        return json_filename, csv_filename

def main():
    """Main execution function."""
    print("=" * 70)
    print("TrustMed AI - Health Forum Data Collection with PRAW")
    print("=" * 70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Initialize collector
    collector = RedditCollector(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)

    all_results = {}

    # Collect data for each disease area
    for disease_name, disease_config in DISEASE_AREAS.items():
        print(f"\n{'=' * 70}")
        print(f"Collecting threads for: {disease_name.upper().replace('_', ' ')}")
        print(f"Target: {disease_config['target_count']} threads")
        print(f"{'=' * 70}")

        threads = collector.collect_threads(disease_config)
        print(f"\n✓ Collected {len(threads)} threads for {disease_name}")

        if threads:
            json_file, csv_file = collector.save_data(threads, disease_name)
            all_results[disease_name] = {
                'count': len(threads),
                'json_file': json_file,
                'csv_file': csv_file
            }

    # Print summary
    print(f"\n{'=' * 70}")
    print("COLLECTION SUMMARY")
    print(f"{'=' * 70}")
    total_threads = sum(r['count'] for r in all_results.values())
    print(f"\nTotal threads collected: {total_threads}")

    for disease_name, results in all_results.items():
        print(f"\n{disease_name.upper().replace('_', ' ')}:")
        print(f"  - Threads: {results['count']}")
        print(f"  - JSON: {results['json_file']}")
        print(f"  - CSV: {results['csv_file']}")

    print(f"\n{'=' * 70}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    main()
