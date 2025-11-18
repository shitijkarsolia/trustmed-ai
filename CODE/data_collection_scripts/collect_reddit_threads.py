#!/usr/bin/env python3
"""
Reddit Health Forum Data Collection Script
Collects discussion threads about Type II Diabetes and Heart Disease/Hypertension
from relevant health subreddits.
"""

import praw
import pandas as pd
import json
import time
from datetime import datetime
import os
import sys

# Configuration
DISEASE_AREAS = {
    'diabetes': {
        'subreddits': ['diabetes', 'diabetes_t2', 'type2diabetes'],
        'keywords': ['type 2', 't2', 'type ii', 'diabetes', 'blood sugar', 'glucose',
                     'insulin resistance', 'metformin', 'hba1c', 'prediabetes'],
        'target_count': 500
    },
    'heart_disease': {
        'subreddits': ['hypertension', 'HeartDisease', 'AskDocs', 'medical'],
        'keywords': ['heart disease', 'hypertension', 'high blood pressure', 'cardiovascular',
                     'cholesterol', 'bp', 'blood pressure', 'heart attack', 'cardiac'],
        'target_count': 500
    }
}

# Get the script directory and set output relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'logs')

class RedditHealthCollector:
    """Collects health-related discussion threads from Reddit."""

    def __init__(self):
        """Initialize Reddit API connection."""
        try:
            # Load credentials from environment variables or config.py
            import os
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'TrustMedAI Health Forum Collector v1.0')
            
            # Fallback to config.py if environment variables not set
            if not client_id or not client_secret:
                try:
                    from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
                    client_id = REDDIT_CLIENT_ID
                    client_secret = REDDIT_CLIENT_SECRET
                    user_agent = REDDIT_USER_AGENT
                except ImportError:
                    print("✗ Reddit API credentials not found!")
                    print("Please set environment variables or create config.py:")
                    print("  - REDDIT_CLIENT_ID")
                    print("  - REDDIT_CLIENT_SECRET")
                    print("  - REDDIT_USER_AGENT (optional)")
                    print("\nVisit: https://www.reddit.com/prefs/apps to create an app.")
                    sys.exit(1)
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.reddit.read_only = True
            print("✓ Reddit API connection established")
        except Exception as e:
            print(f"✗ Error connecting to Reddit API: {e}")
            print("Note: You need to set up Reddit API credentials.")
            print("Visit: https://www.reddit.com/prefs/apps to create an app.")
            sys.exit(1)

    def collect_threads(self, disease_area, limit_per_subreddit=200):
        """
        Collect threads for a specific disease area.

        Args:
            disease_area: Dictionary containing subreddits and keywords
            limit_per_subreddit: Maximum threads to collect per subreddit

        Returns:
            List of thread dictionaries
        """
        threads = []
        seen_ids = set()

        for subreddit_name in disease_area['subreddits']:
            print(f"\nCollecting from r/{subreddit_name}...")

            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Collect from different sorting methods to get diverse content
                for sort_method in ['hot', 'top', 'new']:
                    print(f"  - Fetching {sort_method} posts...")

                    if sort_method == 'hot':
                        posts = subreddit.hot(limit=limit_per_subreddit)
                    elif sort_method == 'top':
                        posts = subreddit.top(time_filter='year', limit=limit_per_subreddit)
                    else:
                        posts = subreddit.new(limit=limit_per_subreddit)

                    for post in posts:
                        # Skip if already collected
                        if post.id in seen_ids:
                            continue

                        # Check if post is relevant to disease area
                        if self._is_relevant(post, disease_area['keywords']):
                            thread_data = self._extract_thread_data(post)
                            threads.append(thread_data)
                            seen_ids.add(post.id)

                        # Add small delay to respect API rate limits
                        time.sleep(0.1)

                    print(f"    Collected {len(threads)} relevant threads so far")

            except Exception as e:
                print(f"  ✗ Error collecting from r/{subreddit_name}: {e}")
                continue

        return threads

    def _is_relevant(self, post, keywords):
        """
        Check if a post is relevant based on keywords.

        Args:
            post: Reddit post object
            keywords: List of relevant keywords

        Returns:
            Boolean indicating relevance
        """
        text = f"{post.title} {post.selftext}".lower()
        return any(keyword.lower() in text for keyword in keywords)

    def _extract_thread_data(self, post):
        """
        Extract relevant data from a Reddit post.

        Args:
            post: Reddit post object

        Returns:
            Dictionary containing thread data
        """
        # Get top comments
        post.comments.replace_more(limit=5)
        comments = []

        for comment in post.comments.list()[:20]:  # Get top 20 comments
            if hasattr(comment, 'body'):
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
            'url': post.url,
            'selftext': post.selftext,
            'upvote_ratio': post.upvote_ratio,
            'comments': comments,
            'collected_at': datetime.now().isoformat()
        }

        return thread_data

    def save_data(self, threads, disease_name):
        """
        Save collected threads to JSON and CSV files.

        Args:
            threads: List of thread dictionaries
            disease_name: Name of the disease area
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save as JSON (full data with comments)
        json_filename = f"{OUTPUT_DIR}/{disease_name}_threads_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved full data to: {json_filename}")

        # Save as CSV (summary without nested comments)
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
                'selftext': thread['selftext'][:500],  # Truncate for CSV
                'upvote_ratio': thread['upvote_ratio']
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
    print("TrustMed AI - Health Forum Data Collection")
    print("=" * 70)
    print(f"\nTarget: 500-1,000 threads on Type II Diabetes and Heart Disease")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directories if they don't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Initialize collector
    collector = RedditHealthCollector()

    all_results = {}

    # Collect data for each disease area
    for disease_name, disease_config in DISEASE_AREAS.items():
        print(f"\n{'=' * 70}")
        print(f"Collecting threads for: {disease_name.upper().replace('_', ' ')}")
        print(f"Target: {disease_config['target_count']} threads")
        print(f"{'=' * 70}")

        threads = collector.collect_threads(disease_config, limit_per_subreddit=200)

        print(f"\n✓ Collected {len(threads)} threads for {disease_name}")

        # Save the data
        if threads:
            json_file, csv_file = collector.save_data(threads, disease_name)
            all_results[disease_name] = {
                'count': len(threads),
                'json_file': json_file,
                'csv_file': csv_file
            }
        else:
            print(f"✗ No threads collected for {disease_name}")

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
    print(f"Collection completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    main()
