#!/usr/bin/env python3
"""
Fetch comments for already collected Reddit threads.
Loads existing JSON files and adds comments to each thread.
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

# Get the script directory and set output relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'data')

class CommentFetcher:
    """Fetches comments for existing Reddit threads."""

    def __init__(self):
        """Initialize the fetcher."""
        print("✓ Comment fetcher initialized")

    def make_request(self, url, max_retries=3):
        """Make HTTP request to Reddit's JSON API with rate limiting."""
        for attempt in range(max_retries):
            try:
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                request.add_header('Accept', 'application/json')
                request.add_header('Accept-Encoding', 'identity')

                with urllib.request.urlopen(request, timeout=15) as response:
                    raw_data = response.read()
                    
                    # Check if response is gzip compressed
                    if raw_data[:2] == b'\x1f\x8b':
                        raw_data = gzip.decompress(raw_data)
                    
                    data = json.loads(raw_data.decode('utf-8'))
                    return data

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 60  # Wait 60, 120, 180 seconds
                    print(f"  ⚠ Rate limited (429). Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif e.code == 403:
                    print(f"  ⚠ Access forbidden (403). Skipping...")
                    return None
                else:
                    if attempt < max_retries - 1:
                        time.sleep(5)
                    else:
                        return None

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    return None

        return None

    def get_post_comments(self, post_url, limit=30, depth=3):
        """
        Get comments for a specific post with nested replies.
        
        Args:
            post_url: Full URL of the post
            limit: Maximum number of top-level comments to collect
            depth: Maximum depth for nested comments (replies)
            
        Returns:
            List of comment dictionaries with nested replies
        """
        # Extract subreddit and post_id from URL
        # URL format: https://reddit.com/r/subreddit/comments/post_id/title/
        try:
            # Convert to JSON API URL
            if '/comments/' in post_url:
                parts = post_url.split('/comments/')
                if len(parts) > 1:
                    post_id = parts[1].split('/')[0]
                    # Build JSON API URL with depth parameter
                    json_url = f"https://www.reddit.com/comments/{post_id}.json?limit={limit}&depth={depth}"
                    
                    data = self.make_request(json_url)
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
        except Exception as e:
            print(f"    Error extracting comments: {e}")
            return []

        return []

    def fetch_comments_for_file(self, json_file, save_interval=25):
        """
        Load a JSON file, fetch comments for all threads, and save updated data.
        
        Args:
            json_file: Path to JSON file with threads
            save_interval: Save every N threads processed
        """
        print(f"\n{'=' * 70}")
        print(f"Processing: {os.path.basename(json_file)}")
        print(f"{'=' * 70}")
        
        # Load existing data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                threads = json.load(f)
        except Exception as e:
            print(f"✗ Error loading file: {e}")
            return

        total_threads = len(threads)
        # Check if threads have comments (not just empty arrays)
        threads_with_comments = sum(1 for t in threads 
                                   if t.get('comments') and len(t.get('comments', [])) > 0)
        
        print(f"Total threads: {total_threads}")
        print(f"Threads already with comments: {threads_with_comments}")
        print(f"Threads needing comments: {total_threads - threads_with_comments}")
        
        if threads_with_comments == total_threads:
            print("✓ All threads already have comments!")
            return

        # Process threads - filter out threads that already have comments first
        threads_needing_comments = []
        for thread in threads:
            existing_comments = thread.get('comments', [])
            num_collected = thread.get('num_collected_comments', 0)
            thread_url = thread.get('url', '')
            
            # Only add to list if it needs comments AND has a URL
            if not ((existing_comments and len(existing_comments) > 0) or num_collected > 0) and thread_url:
                threads_needing_comments.append(thread)
        
        threads_to_process = len(threads_needing_comments)
        print(f"  Threads needing comments: {threads_to_process}")
        
        if threads_to_process == 0:
            print("✓ All threads already have comments!")
            return

        # Process only threads that need comments
        processed = 0
        updated = 0
        last_save = 0

        for i, thread in enumerate(threads_needing_comments):
            thread_url = thread.get('url', '')
            
            # Make API call only here
            processed += 1
            print(f"  [{processed}/{threads_to_process}] Fetching comments for: {thread['title'][:60]}...")
            comments = self.get_post_comments(thread_url, limit=30, depth=3)
            
            if comments:
                thread['comments'] = comments
                # Count total comments including nested replies
                def count_all_comments(comment_list):
                    total = len(comment_list)
                    for comment in comment_list:
                        if comment.get('replies'):
                            total += count_all_comments(comment['replies'])
                    return total
                
                total_comment_count = count_all_comments(comments)
                thread['num_collected_comments'] = total_comment_count
                updated += 1
                print(f"    ✓ Found {len(comments)} top-level comments ({total_comment_count} total including replies)")
            else:
                thread['comments'] = []
                thread['num_collected_comments'] = 0
                print(f"    - No comments found")

            # Incremental save (only count threads we actually processed)
            if processed - last_save >= save_interval:
                self._save_file(threads, json_file)
                last_save = processed
                print(f"    💾 Saved progress ({processed}/{threads_to_process})")

            # Rate limiting - wait 2-3 seconds between requests (reduced for speed)
            # Don't wait if this is the last thread
            if processed < threads_to_process:
                wait_time = random.uniform(2, 3)
                time.sleep(wait_time)

        # Final save
        if processed > last_save:
            self._save_file(threads, json_file)
        
        print(f"\n✓ Completed: {updated} threads updated with comments")
        print(f"✓ Final save: {json_file}")

    def _save_file(self, threads, original_file):
        """Save updated threads to file."""
        # Save to same file (overwrite)
        with open(original_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2, ensure_ascii=False)
        
        # Also update CSV if it exists
        csv_file = original_file.replace('.json', '.csv')
        if os.path.exists(csv_file):
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
            df.to_csv(csv_file, index=False, encoding='utf-8')

def main():
    """Main execution function."""
    print("=" * 70)
    print("Reddit Comment Fetcher")
    print("=" * 70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This script fetches comments for already collected threads.")
    print("Rate limiting: 3-5 seconds between requests\n")

    # Find all JSON files in data directory
    json_files = glob.glob(f"{OUTPUT_DIR}/*_threads_*.json")
    
    # Filter out incremental files (we want timestamped ones)
    json_files = [f for f in json_files if 'incremental' not in f]
    
    if not json_files:
        print(f"✗ No JSON files found in {OUTPUT_DIR}")
        print("  Looking for files matching: *_threads_*.json")
        return

    print(f"Found {len(json_files)} JSON file(s) to process:")
    for f in json_files:
        print(f"  - {os.path.basename(f)}")

    fetcher = CommentFetcher()

    # Process each file
    for json_file in json_files:
        fetcher.fetch_comments_for_file(json_file, save_interval=25)
        
        # Wait between files
        if json_file != json_files[-1]:
            wait_time = random.uniform(10, 15)
            print(f"\nWaiting {wait_time:.1f} seconds before next file...")
            time.sleep(wait_time)

    print(f"\n{'=' * 70}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    main()

