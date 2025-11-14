#!/usr/bin/env python3
"""
Reddit Health Forum Data Collection Script (Public API)
Uses Reddit's public JSON API - no authentication required.
Collects discussion threads about Type II Diabetes and Heart Disease/Hypertension.
"""

import json
import time
from datetime import datetime
import os
import sys
import urllib.request
import urllib.error
import pandas as pd

# Configuration
DISEASE_AREAS = {
    'diabetes': {
        'subreddits': ['diabetes', 'diabetes_t2'],
        'search_terms': [
            'type 2 diabetes',
            'T2 diabetes',
            'diabetes medication',
            'blood sugar management',
            'metformin',
            'diabetes symptoms'
        ],
        'target_count': 500
    },
    'heart_disease': {
        'subreddits': ['hypertension', 'HeartDisease'],
        'search_terms': [
            'high blood pressure',
            'hypertension treatment',
            'heart disease',
            'cardiovascular',
            'blood pressure medication',
            'heart health'
        ],
        'target_count': 500
    }
}

OUTPUT_DIR = '/home/user/trustmed-ai/data_collection/data'
LOG_DIR = '/home/user/trustmed-ai/data_collection/logs'

class RedditPublicCollector:
    """Collects health-related discussion threads from Reddit using public JSON API."""

    def __init__(self):
        """Initialize the collector."""
        self.user_agent = 'TrustMedAI Health Forum Collector v1.0'
        print("✓ Reddit Public API collector initialized")

    def make_request(self, url, max_retries=3):
        """
        Make HTTP request to Reddit's JSON API.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            JSON response data
        """
        for attempt in range(max_retries):
            try:
                request = urllib.request.Request(url)
                # Add comprehensive headers to mimic a browser
                request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                request.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
                request.add_header('Accept-Language', 'en-US,en;q=0.9')
                request.add_header('Accept-Encoding', 'gzip, deflate')
                request.add_header('DNT', '1')
                request.add_header('Connection', 'keep-alive')
                request.add_header('Upgrade-Insecure-Requests', '1')

                with urllib.request.urlopen(request, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return data

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    print(f"  Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif e.code == 403:
                    print(f"  Access forbidden (403). Reddit may be blocking automated access.")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3
                        print(f"  Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return None
                else:
                    print(f"  HTTP Error {e.code}: {e.reason}")
                    return None

            except Exception as e:
                print(f"  Error making request: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None

        return None

    def collect_subreddit_posts(self, subreddit_name, limit=100, sort='hot'):
        """
        Collect posts from a specific subreddit.

        Args:
            subreddit_name: Name of the subreddit
            limit: Number of posts to collect
            sort: Sorting method (hot, new, top)

        Returns:
            List of post data dictionaries
        """
        posts = []
        after = None
        collected = 0

        while collected < limit:
            # Build URL
            url = f"https://www.reddit.com/r/{subreddit_name}/{sort}.json?limit=100"
            if after:
                url += f"&after={after}"

            # Make request
            data = self.make_request(url)
            if not data or 'data' not in data:
                break

            children = data['data'].get('children', [])
            if not children:
                break

            for child in children:
                post_data = child.get('data', {})
                posts.append(post_data)
                collected += 1

                if collected >= limit:
                    break

            after = data['data'].get('after')
            if not after:
                break

            # Respect rate limits
            time.sleep(2)

        return posts

    def search_subreddit(self, subreddit_name, query, limit=100):
        """
        Search for posts in a subreddit.

        Args:
            subreddit_name: Name of the subreddit
            query: Search query
            limit: Maximum number of results

        Returns:
            List of post data dictionaries
        """
        posts = []
        after = None
        collected = 0

        while collected < limit:
            # Build search URL
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/r/{subreddit_name}/search.json?q={encoded_query}&restrict_sr=1&limit=100&sort=relevance"

            if after:
                url += f"&after={after}"

            # Make request
            data = self.make_request(url)
            if not data or 'data' not in data:
                break

            children = data['data'].get('children', [])
            if not children:
                break

            for child in children:
                post_data = child.get('data', {})
                posts.append(post_data)
                collected += 1

                if collected >= limit:
                    break

            after = data['data'].get('after')
            if not after:
                break

            # Respect rate limits
            time.sleep(2)

        return posts

    def get_post_comments(self, subreddit_name, post_id, limit=20):
        """
        Get comments for a specific post.

        Args:
            subreddit_name: Name of the subreddit
            post_id: ID of the post
            limit: Maximum number of comments to collect

        Returns:
            List of comment dictionaries
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}.json?limit={limit}"
        data = self.make_request(url)

        if not data or len(data) < 2:
            return []

        comments = []
        comment_data = data[1].get('data', {}).get('children', [])

        for comment in comment_data:
            if comment.get('kind') == 't1':  # Comment type
                comment_info = comment.get('data', {})
                comments.append({
                    'author': comment_info.get('author', '[deleted]'),
                    'body': comment_info.get('body', ''),
                    'score': comment_info.get('score', 0),
                    'created_utc': datetime.fromtimestamp(
                        comment_info.get('created_utc', 0)
                    ).isoformat()
                })

        return comments[:limit]

    def collect_threads(self, disease_area):
        """
        Collect threads for a specific disease area.

        Args:
            disease_area: Dictionary containing subreddits and search terms

        Returns:
            List of thread dictionaries
        """
        threads = []
        seen_ids = set()

        # Collect from each subreddit
        for subreddit_name in disease_area['subreddits']:
            print(f"\nCollecting from r/{subreddit_name}...")

            # Method 1: Get hot posts
            print("  - Fetching hot posts...")
            hot_posts = self.collect_subreddit_posts(subreddit_name, limit=100, sort='hot')
            for post in hot_posts:
                if post.get('id') not in seen_ids:
                    thread = self._process_post(post, subreddit_name)
                    if thread:
                        threads.append(thread)
                        seen_ids.add(post.get('id'))
            print(f"    Total threads: {len(threads)}")

            # Method 2: Get top posts
            print("  - Fetching top posts...")
            top_posts = self.collect_subreddit_posts(subreddit_name, limit=100, sort='top')
            for post in top_posts:
                if post.get('id') not in seen_ids:
                    thread = self._process_post(post, subreddit_name)
                    if thread:
                        threads.append(thread)
                        seen_ids.add(post.get('id'))
            print(f"    Total threads: {len(threads)}")

            # Method 3: Search with specific terms
            for search_term in disease_area['search_terms'][:3]:  # Limit searches
                print(f"  - Searching for '{search_term}'...")
                search_results = self.search_subreddit(subreddit_name, search_term, limit=50)
                for post in search_results:
                    if post.get('id') not in seen_ids:
                        thread = self._process_post(post, subreddit_name)
                        if thread:
                            threads.append(thread)
                            seen_ids.add(post.get('id'))
                print(f"    Total threads: {len(threads)}")

        return threads

    def _process_post(self, post, subreddit_name):
        """
        Process a Reddit post into structured thread data.

        Args:
            post: Raw post data from Reddit API
            subreddit_name: Name of the subreddit

        Returns:
            Dictionary containing thread data
        """
        try:
            post_id = post.get('id')
            if not post_id:
                return None

            # Get comments for the post
            comments = self.get_post_comments(subreddit_name, post_id, limit=20)

            thread_data = {
                'id': post_id,
                'title': post.get('title', ''),
                'author': post.get('author', '[deleted]'),
                'subreddit': post.get('subreddit', subreddit_name),
                'created_utc': datetime.fromtimestamp(
                    post.get('created_utc', 0)
                ).isoformat(),
                'score': post.get('score', 0),
                'num_comments': post.get('num_comments', 0),
                'url': f"https://reddit.com{post.get('permalink', '')}",
                'selftext': post.get('selftext', ''),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'comments': comments,
                'collected_at': datetime.now().isoformat()
            }

            return thread_data

        except Exception as e:
            print(f"    Error processing post: {e}")
            return None

    def save_data(self, threads, disease_name):
        """
        Save collected threads to JSON and CSV files.

        Args:
            threads: List of thread dictionaries
            disease_name: Name of the disease area

        Returns:
            Tuple of (json_filename, csv_filename)
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
                'selftext': thread['selftext'][:500] if thread['selftext'] else '',
                'upvote_ratio': thread['upvote_ratio'],
                'num_collected_comments': len(thread.get('comments', []))
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
    print("TrustMed AI - Health Forum Data Collection (Public API)")
    print("=" * 70)
    print(f"\nTarget: 500-1,000 threads on Type II Diabetes and Heart Disease")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Initialize collector
    collector = RedditPublicCollector()

    all_results = {}

    # Collect data for each disease area
    for disease_name, disease_config in DISEASE_AREAS.items():
        print(f"\n{'=' * 70}")
        print(f"Collecting threads for: {disease_name.upper().replace('_', ' ')}")
        print(f"Target: {disease_config['target_count']} threads")
        print(f"{'=' * 70}")

        threads = collector.collect_threads(disease_config)

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

    return total_threads >= 500

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
