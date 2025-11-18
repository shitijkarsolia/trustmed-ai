#!/usr/bin/env python3
"""
Reddit Health Forum Data Collection Script - HTML Web Scraping
Scrapes Reddit HTML pages directly without API authentication.
Collects discussion threads about Type II Diabetes and Heart Disease/Hypertension.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import os
import sys
import pandas as pd
import re

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

# Get the script directory and set output relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'data_collection', 'logs')

class RedditHTMLScraper:
    """Scrapes Reddit HTML pages directly without API."""

    def __init__(self):
        """Initialize the scraper with browser-like headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        print("✓ Reddit HTML scraper initialized")

    def get_page(self, url, max_retries=3):
        """
        Fetch a Reddit page with retries and rate limiting.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            BeautifulSoup object or None
        """
        for attempt in range(max_retries):
            try:
                # Random delay to avoid detection (2-5 seconds)
                if attempt > 0:
                    time.sleep(random.uniform(2, 5))
                else:
                    time.sleep(random.uniform(1, 3))

                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                return soup

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    print(f"  Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif e.response.status_code == 403:
                    print(f"  Access forbidden (403). Waiting before retry...")
                    time.sleep(5)
                else:
                    print(f"  HTTP Error {e.response.status_code}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                    else:
                        return None

            except Exception as e:
                print(f"  Error fetching page: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    return None

        return None

    def extract_post_data(self, post_element):
        """
        Extract data from a Reddit post element.

        Args:
            post_element: BeautifulSoup element containing post data

        Returns:
            Dictionary with post data or None
        """
        try:
            # Try to find post data in various ways
            # Reddit uses different structures, so we try multiple selectors
            
            # Method 1: Look for data attributes
            post_id = post_element.get('id', '').replace('t3_', '')
            if not post_id:
                # Try to extract from link
                link = post_element.find('a', {'data-click-id': 'body'})
                if link and link.get('href'):
                    match = re.search(r'/comments/([a-z0-9]+)/', link.get('href', ''))
                    if match:
                        post_id = match.group(1)

            # Extract title
            title_elem = post_element.find('h3') or post_element.find('a', {'data-click-id': 'body'})
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Extract author
            author_elem = post_element.find('a', href=re.compile(r'/user/'))
            author = author_elem.get_text(strip=True) if author_elem else '[deleted]'

            # Extract score
            score_elem = post_element.find('button', {'aria-label': re.compile(r'vote|score')})
            score = 0
            if score_elem:
                score_text = score_elem.get_text(strip=True)
                # Try to extract number from text
                score_match = re.search(r'(\d+)', score_text.replace(',', ''))
                if score_match:
                    score = int(score_match.group(1))

            # Extract number of comments
            comments_elem = post_element.find('a', href=re.compile(r'/comments/'))
            num_comments = 0
            if comments_elem:
                comments_text = comments_elem.get_text(strip=True)
                comments_match = re.search(r'(\d+)', comments_text.replace(',', ''))
                if comments_match:
                    num_comments = int(comments_match.group(1))

            # Extract post text/selftext
            selftext = ''
            text_elem = post_element.find('div', {'data-test-id': 'post-content'})
            if not text_elem:
                text_elem = post_element.find('div', class_=re.compile(r'post|selftext'))
            if text_elem:
                selftext = text_elem.get_text(strip=True)

            # Extract URL
            url = ''
            link_elem = post_element.find('a', {'data-click-id': 'body'})
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    url = f"https://www.reddit.com{href}"
                else:
                    url = href

            # Extract subreddit
            subreddit_elem = post_element.find('a', href=re.compile(r'/r/[^/]+'))
            subreddit = ''
            if subreddit_elem:
                match = re.search(r'/r/([^/]+)', subreddit_elem.get('href', ''))
                if match:
                    subreddit = match.group(1)

            if not post_id or not title:
                return None

            return {
                'id': post_id,
                'title': title,
                'author': author,
                'subreddit': subreddit,
                'score': score,
                'num_comments': num_comments,
                'url': url,
                'selftext': selftext,
                'upvote_ratio': 0.0,  # Not easily available in HTML
                'created_utc': datetime.now().isoformat(),  # Approximate
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"    Error extracting post data: {e}")
            return None

    def get_post_comments(self, post_url):
        """
        Get comments from a post page.

        Args:
            post_url: URL of the post

        Returns:
            List of comment dictionaries
        """
        comments = []
        try:
            soup = self.get_page(post_url)
            if not soup:
                return comments

            # Find comment elements
            comment_elements = soup.find_all('div', {'data-testid': 'comment'})
            if not comment_elements:
                # Try alternative selectors
                comment_elements = soup.find_all('div', class_=re.compile(r'comment'))

            for comment_elem in comment_elements[:30]:  # Limit to 30 comments
                try:
                    # Extract author
                    author_elem = comment_elem.find('a', href=re.compile(r'/user/'))
                    author = author_elem.get_text(strip=True) if author_elem else '[deleted]'

                    # Extract comment body
                    body_elem = comment_elem.find('div', {'data-testid': 'comment'})
                    if not body_elem:
                        body_elem = comment_elem.find('div', class_=re.compile(r'markdown|comment-body'))
                    body = body_elem.get_text(strip=True) if body_elem else ''

                    # Extract score
                    score = 0
                    score_elem = comment_elem.find('button', {'aria-label': re.compile(r'vote|score')})
                    if score_elem:
                        score_text = score_elem.get_text(strip=True)
                        score_match = re.search(r'(\d+)', score_text.replace(',', ''))
                        if score_match:
                            score = int(score_match.group(1))

                    if body:
                        comments.append({
                            'author': author,
                            'body': body,
                            'score': score,
                            'created_utc': datetime.now().isoformat()
                        })

                except Exception as e:
                    continue

        except Exception as e:
            print(f"    Error getting comments: {e}")

        return comments

    def scrape_subreddit(self, subreddit_name, sort='hot', limit=100):
        """
        Scrape posts from a subreddit.

        Args:
            subreddit_name: Name of the subreddit
            sort: Sorting method (hot, new, top)
            limit: Maximum number of posts to collect

        Returns:
            List of post dictionaries
        """
        posts = []
        seen_ids = set()
        page_count = 0
        max_pages = (limit // 25) + 2  # Reddit shows ~25 posts per page

        while len(posts) < limit and page_count < max_pages:
            # Build URL
            if sort == 'top':
                url = f"https://www.reddit.com/r/{subreddit_name}/top/?t=month"
            elif sort == 'new':
                url = f"https://www.reddit.com/r/{subreddit_name}/new/"
            else:
                url = f"https://www.reddit.com/r/{subreddit_name}/hot/"

            if page_count > 0:
                url += f"?count={page_count * 25}&after={seen_ids.pop() if seen_ids else ''}"

            print(f"    Fetching page {page_count + 1} ({sort})...")

            soup = self.get_page(url)
            if not soup:
                print(f"    Failed to fetch page {page_count + 1}")
                break

            # Find post elements
            # Reddit uses different structures, try multiple selectors
            post_elements = soup.find_all('div', {'data-testid': 'post-container'})
            if not post_elements:
                post_elements = soup.find_all('div', id=re.compile(r't3_'))
            if not post_elements:
                post_elements = soup.find_all('shreddit-post')

            if not post_elements:
                print(f"    No posts found on page {page_count + 1}")
                break

            page_posts = 0
            for post_elem in post_elements:
                post_data = self.extract_post_data(post_elem)
                if post_data and post_data['id'] not in seen_ids:
                    post_data['subreddit'] = subreddit_name
                    posts.append(post_data)
                    seen_ids.add(post_data['id'])
                    page_posts += 1

                    if len(posts) >= limit:
                        break

            print(f"    Found {page_posts} new posts (total: {len(posts)})")

            if page_posts == 0:
                break

            page_count += 1
            time.sleep(random.uniform(2, 4))  # Be respectful with delays

        return posts

    def collect_threads(self, disease_area):
        """
        Collect threads for a specific disease area.

        Args:
            disease_area: Dictionary containing subreddits and keywords

        Returns:
            List of thread dictionaries with comments
        """
        all_threads = []
        seen_ids = set()

        for subreddit_name in disease_area['subreddits']:
            print(f"\nScraping r/{subreddit_name}...")

            # Try different sort methods
            for sort_method in ['hot', 'top', 'new']:
                print(f"  - Fetching {sort_method} posts...")
                posts = self.scrape_subreddit(subreddit_name, sort=sort_method, limit=150)

                for post in posts:
                    if post['id'] in seen_ids:
                        continue

                    # Check relevance
                    text = f"{post['title']} {post['selftext']}".lower()
                    if any(keyword.lower() in text for keyword in disease_area['keywords']):
                        # Get comments
                        if post['url']:
                            print(f"    Fetching comments for: {post['title'][:50]}...")
                            comments = self.get_post_comments(post['url'])
                            post['comments'] = comments
                            post['num_collected_comments'] = len(comments)
                        else:
                            post['comments'] = []
                            post['num_collected_comments'] = 0

                        all_threads.append(post)
                        seen_ids.add(post['id'])

                        if len(all_threads) >= disease_area['target_count']:
                            break

                        # Rate limiting
                        time.sleep(random.uniform(2, 4))

                if len(all_threads) >= disease_area['target_count']:
                    break

                print(f"    Total relevant threads: {len(all_threads)}")

            if len(all_threads) >= disease_area['target_count']:
                break

        return all_threads

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
                'created_utc': thread.get('created_utc', ''),
                'score': thread['score'],
                'num_comments': thread['num_comments'],
                'url': thread['url'],
                'selftext': thread['selftext'][:500] if thread['selftext'] else '',
                'upvote_ratio': thread.get('upvote_ratio', 0),
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
    print("TrustMed AI - Reddit HTML Web Scraper")
    print("=" * 70)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Note: This script scrapes Reddit HTML directly (no API required)")
    print("      Collection may take 1-2 hours due to rate limiting.\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    scraper = RedditHTMLScraper()
    all_results = {}

    # Collect data for each disease area
    for disease_name, disease_config in DISEASE_AREAS.items():
        print(f"\n{'=' * 70}")
        print(f"Collecting threads for: {disease_name.upper().replace('_', ' ')}")
        print(f"Target: {disease_config['target_count']} threads")
        print(f"{'=' * 70}")

        threads = scraper.collect_threads(disease_config)
        print(f"\n✓ Collected {len(threads)} threads for {disease_name}")

        if threads:
            json_file, csv_file = scraper.save_data(threads, disease_name)
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

