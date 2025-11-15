#!/usr/bin/env python3
"""
Reddit Health Forum Data Collection Script (Public API)
Uses Reddit's public JSON API - no authentication required.
Collects discussion threads about Type II Diabetes and Heart Disease/Hypertension.
"""

import json
import time
import gzip
import random
import glob
from datetime import datetime
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import pandas as pd

# Configuration
DISEASE_AREAS = {
    'diabetes': {
        'subreddits': ['diabetes', 'diabetes_t2', 'type2diabetes', 'prediabetes', 'diabetes_management'],
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
        'subreddits': ['hypertension', 'HeartDisease', 'Cardiology', 'AskCardiology', 'cholesterol'],
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

# Get the script directory and set output relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'logs')

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
                request.add_header('Accept', 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
                request.add_header('Accept-Language', 'en-US,en;q=0.9')
                # Don't request gzip to avoid decompression issues, or handle it properly
                request.add_header('Accept-Encoding', 'identity')
                request.add_header('DNT', '1')
                request.add_header('Connection', 'keep-alive')
                request.add_header('Upgrade-Insecure-Requests', '1')

                with urllib.request.urlopen(request, timeout=15) as response:
                    # Read the response
                    raw_data = response.read()
                    
                    # Check if response is gzip compressed (sometimes servers ignore Accept-Encoding)
                    if raw_data[:2] == b'\x1f\x8b':  # Gzip magic number
                        raw_data = gzip.decompress(raw_data)
                    
                    # Decode and parse JSON
                    data = json.loads(raw_data.decode('utf-8'))
                    return data

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 30  # Much longer wait for rate limits
                    print(f"  ⚠ Rate limited (429). Waiting {wait_time} seconds...")
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

    def collect_subreddit_posts(self, subreddit_name, limit=100, sort='hot', max_pages=5):
        """
        Collect posts from a specific subreddit.

        Args:
            subreddit_name: Name of the subreddit
            limit: Number of posts to collect
            sort: Sorting method (hot, new, top)
            max_pages: Maximum number of pages to fetch (default 5)

        Returns:
            List of post data dictionaries
        """
        posts = []
        after = None
        collected = 0
        page_count = 0

        while collected < limit and page_count < max_pages:
            # Build URL - limit to 25 posts per page for better rate limiting
            url = f"https://www.reddit.com/r/{subreddit_name}/{sort}.json?limit=25"
            if after:
                url += f"&after={after}"

            print(f"      Fetching page {page_count + 1}/{max_pages}...")

            # Make request
            data = self.make_request(url)
            if not data or 'data' not in data:
                print(f"      Failed to fetch page {page_count + 1}")
                break

            children = data['data'].get('children', [])
            if not children:
                print(f"      No more posts found")
                break

            page_posts = 0
            for child in children:
                post_data = child.get('data', {})
                posts.append(post_data)
                collected += 1
                page_posts += 1

                if collected >= limit:
                    break

            print(f"      Found {page_posts} posts on page {page_count + 1} (total: {collected})")

            after = data['data'].get('after')
            if not after:
                print(f"      No more pages available")
                break

            page_count += 1
            
            # Reduced wait time for speed (still safe)
            if page_count < max_pages:
                wait_time = random.uniform(2, 4)
                print(f"      Waiting {wait_time:.1f} seconds before next page...")
                time.sleep(wait_time)

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

    def get_post_comments(self, subreddit_name, post_id, limit=30, depth=2):
        """
        Get comments for a specific post with nested replies.

        Args:
            subreddit_name: Name of the subreddit
            post_id: ID of the post
            limit: Maximum number of top-level comments to collect
            depth: Maximum depth for nested comments (replies)

        Returns:
            List of comment dictionaries with nested replies
        """
        url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}.json?limit={limit}&depth={depth}"
        data = self.make_request(url)

        if not data or len(data) < 2:
            return []

        comments = []
        comment_data = data[1].get('data', {}).get('children', [])

        def extract_comment(comment_obj, current_depth=0, max_depth=depth):
            """Recursively extract comment and its replies."""
            if comment_obj.get('kind') != 't1':  # Not a comment
                return None
            
            comment_info = comment_obj.get('data', {})
            
            # Extract this comment
            comment = {
                'author': comment_info.get('author', '[deleted]'),
                'body': comment_info.get('body', ''),
                'score': comment_info.get('score', 0),
                'created_utc': datetime.fromtimestamp(
                    comment_info.get('created_utc', 0)
                ).isoformat(),
                'replies': []
            }
            
            # Extract nested replies if within depth limit
            if current_depth < max_depth:
                replies_data = comment_info.get('replies', {})
                if replies_data and isinstance(replies_data, dict):
                    reply_children = replies_data.get('data', {}).get('children', [])
                    for reply_obj in reply_children:
                        reply = extract_comment(reply_obj, current_depth + 1, max_depth)
                        if reply:
                            comment['replies'].append(reply)
            
            return comment

        for comment_obj in comment_data[:limit]:
            comment = extract_comment(comment_obj)
            if comment:
                comments.append(comment)

        return comments

    def collect_threads(self, disease_area, disease_name, additional_count=500):
        """
        Collect additional threads for a specific disease area with incremental saving.
        Skips subreddits that have already been scraped.

        Args:
            disease_area: Dictionary containing subreddits and search terms
            disease_name: Name of the disease area (for saving files)
            additional_count: Number of additional threads to collect

        Returns:
            List of thread dictionaries (existing + new)
        """
        # Try to load existing data to avoid duplicates
        threads, seen_ids, scraped_subreddits = self._load_existing_data(disease_name)
        initial_count = len(threads)
        target_count = initial_count + additional_count
        
        if initial_count > 0:
            print(f"  Loaded {initial_count} existing threads")
            print(f"  Already scraped subreddits: {scraped_subreddits}")
            print(f"  Target: Collect {additional_count} more threads (total: {target_count})")
        else:
            print(f"  Starting fresh collection")
            print(f"  Target: {additional_count} threads")

        # Filter out already-scraped subreddits
        available_subreddits = [sub for sub in disease_area['subreddits'] 
                               if sub not in scraped_subreddits]
        
        if not available_subreddits:
            print(f"  ⚠ All subreddits already scraped! No new subreddits to collect from.")
            return threads
        
        print(f"  New subreddits to scrape: {available_subreddits}")

        save_interval = 25  # Save every 25 threads
        last_save_count = initial_count

        # Collect from each NEW subreddit only
        for subreddit_name in available_subreddits:
            print(f"\nCollecting from r/{subreddit_name}...")

            # Check if we've reached target
            if len(threads) >= target_count:
                print(f"  ✓ Reached target of {target_count} threads!")
                break

            # Method 1: Get hot posts (15 pages = ~375 posts for faster collection)
            print("  - Fetching hot posts (15 pages max)...")
            hot_posts = self.collect_subreddit_posts(subreddit_name, limit=375, sort='hot', max_pages=15)
            new_threads_this_batch = 0
            for post in hot_posts:
                if len(threads) >= target_count:
                    break
                    
                if post.get('id') not in seen_ids:
                    # Don't fetch comments during collection to save time
                    thread = self._process_post(post, subreddit_name, fetch_comments=False)
                    if thread:
                        threads.append(thread)
                        seen_ids.add(post.get('id'))
                        new_threads_this_batch += 1
                        
                        # Incremental save every N threads
                        if len(threads) - last_save_count >= save_interval:
                            self._save_incremental(threads, disease_name)
                            last_save_count = len(threads)
                            print(f"    💾 Saved {len(threads)} threads (incremental save)")
                    
                    # Shorter delay when not fetching comments
                    time.sleep(random.uniform(1, 2))
            
            print(f"    Added {new_threads_this_batch} new threads (total: {len(threads)})")
            
            # Save after each subreddit batch
            if len(threads) > last_save_count:
                self._save_incremental(threads, disease_name)
                last_save_count = len(threads)
            
            # Wait between different sort methods (reduced for speed)
            if len(threads) < target_count:
                wait_time = random.uniform(5, 8)
                print(f"  Waiting {wait_time:.1f} seconds before next batch...")
                time.sleep(wait_time)

            # Method 2: Get top posts (15 pages = ~375 posts for faster collection)
            if len(threads) < target_count:
                print("  - Fetching top posts (15 pages max)...")
                top_posts = self.collect_subreddit_posts(subreddit_name, limit=375, sort='top', max_pages=15)
                new_threads_this_batch = 0
                for post in top_posts:
                    if len(threads) >= target_count:
                        break
                        
                    if post.get('id') not in seen_ids:
                        # Don't fetch comments during collection to save time
                        thread = self._process_post(post, subreddit_name, fetch_comments=False)
                        if thread:
                            threads.append(thread)
                            seen_ids.add(post.get('id'))
                            new_threads_this_batch += 1
                            
                            # Incremental save every N threads
                            if len(threads) - last_save_count >= save_interval:
                                self._save_incremental(threads, disease_name)
                                last_save_count = len(threads)
                                print(f"    💾 Saved {len(threads)} threads (incremental save)")
                        
                        time.sleep(random.uniform(1, 2))
                
                print(f"    Added {new_threads_this_batch} new threads (total: {len(threads)})")
                
                # Save after each subreddit batch
                if len(threads) > last_save_count:
                    self._save_incremental(threads, disease_name)
                    last_save_count = len(threads)
                
                if len(threads) < target_count:
                    wait_time = random.uniform(5, 8)
                    print(f"  Waiting {wait_time:.1f} seconds before next batch...")
                    time.sleep(wait_time)
            
            # Method 3: Get new posts (10 pages = ~250 posts for faster collection)
            if len(threads) < target_count:
                print("  - Fetching new posts (10 pages max)...")
                new_posts = self.collect_subreddit_posts(subreddit_name, limit=250, sort='new', max_pages=10)
                new_threads_this_batch = 0
                for post in new_posts:
                    if len(threads) >= target_count:
                        break
                        
                    if post.get('id') not in seen_ids:
                        # Don't fetch comments during collection to save time
                        thread = self._process_post(post, subreddit_name, fetch_comments=False)
                        if thread:
                            threads.append(thread)
                            seen_ids.add(post.get('id'))
                            new_threads_this_batch += 1
                            
                            # Incremental save every N threads
                            if len(threads) - last_save_count >= save_interval:
                                self._save_incremental(threads, disease_name)
                                last_save_count = len(threads)
                                print(f"    💾 Saved {len(threads)} threads (incremental save)")
                        
                        time.sleep(random.uniform(1, 2))
                
                print(f"    Added {new_threads_this_batch} new threads (total: {len(threads)})")
                
                # Save after each subreddit batch
                if len(threads) > last_save_count:
                    self._save_incremental(threads, disease_name)
                    last_save_count = len(threads)

        # Final save
        if len(threads) > last_save_count:
            self._save_incremental(threads, disease_name)

        return threads

    def _process_post(self, post, subreddit_name, fetch_comments=False):
        """
        Process a Reddit post into structured thread data.

        Args:
            post: Raw post data from Reddit API
            subreddit_name: Name of the subreddit
            fetch_comments: Whether to fetch comments with nested replies

        Returns:
            Dictionary containing thread data
        """
        try:
            post_id = post.get('id')
            if not post_id:
                return None

            # Get comments with nested replies if requested
            comments = []
            if fetch_comments:
                comments = self.get_post_comments(subreddit_name, post_id, limit=30, depth=3)
                # Wait after fetching comments (longer since we're getting nested replies)
                time.sleep(random.uniform(5, 7))

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

    def _load_existing_data(self, disease_name):
        """
        Load existing data files to continue collection without duplicates.
        Prioritizes timestamped files over incremental files.
        Also identifies which subreddits have already been scraped.
        
        Args:
            disease_name: Name of the disease area
            
        Returns:
            Tuple of (threads list, seen_ids set, scraped_subreddits set)
        """
        threads = []
        seen_ids = set()
        scraped_subreddits = set()
        
        # Look for existing files for this disease
        # Priority: timestamped files > incremental files
        timestamped_files = glob.glob(f"{OUTPUT_DIR}/{disease_name}_threads_*.json")
        timestamped_files = [f for f in timestamped_files if 'incremental' not in f]
        
        incremental_file = os.path.join(OUTPUT_DIR, f"{disease_name}_threads_incremental.json")
        
        existing_files = []
        
        # Prefer timestamped files
        if timestamped_files:
            existing_files.extend(timestamped_files)
        
        # Fall back to incremental file
        if os.path.exists(incremental_file):
            existing_files.append(incremental_file)
        
        if existing_files:
            # Use the most recent file
            latest_file = max(existing_files, key=os.path.getmtime)
            try:
                print(f"  Loading existing data from: {os.path.basename(latest_file)}")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    threads = json.load(f)
                    # Track both thread IDs and comment IDs to avoid re-fetching
                    seen_ids = {thread['id'] for thread in threads}
                    # Track which subreddits have already been scraped
                    scraped_subreddits = {thread.get('subreddit', '') for thread in threads if thread.get('subreddit')}
                    # Also track threads that already have comments
                    threads_with_comments = {thread['id'] for thread in threads 
                                           if thread.get('comments') and len(thread.get('comments', [])) > 0}
                    print(f"  Found {len(threads)} existing threads")
                    print(f"  {len(threads_with_comments)} threads already have comments")
                    return threads, seen_ids, scraped_subreddits
            except Exception as e:
                print(f"  Warning: Could not load existing data: {e}")
        
        return [], set(), set()

    def _save_incremental(self, threads, disease_name):
        """
        Save threads incrementally to timestamped files (for safety during collection).
        Creates temporary timestamped files that can be cleaned up later.

        Args:
            threads: List of thread dictionaries
            disease_name: Name of the disease area
        """
        # Use timestamped filename for incremental saves (can be cleaned up later)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"{OUTPUT_DIR}/{disease_name}_threads_incremental_{timestamp}.json"
        
        # Save as JSON (full data)
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2, ensure_ascii=False)

        # Save as CSV (summary)
        csv_data = []
        for thread in threads:
            # Count total comments including nested replies
            def count_comments(comment_list):
                total = len(comment_list)
                for comment in comment_list:
                    if isinstance(comment, dict) and comment.get('replies'):
                        total += count_comments(comment['replies'])
                return total
            
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
                'num_collected_comments': count_comments(thread.get('comments', []))
            }
            csv_data.append(csv_row)

        df = pd.DataFrame(csv_data)
        csv_filename = f"{OUTPUT_DIR}/{disease_name}_threads_incremental_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')

    def save_data(self, threads, disease_name):
        """
        Final save with timestamp (called at the end of collection).

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
        print(f"\n✓ Saved final data to: {json_filename}")

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
        print(f"✓ Saved final summary to: {csv_filename}")

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

        threads = collector.collect_threads(disease_config, disease_name, additional_count=500)

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
