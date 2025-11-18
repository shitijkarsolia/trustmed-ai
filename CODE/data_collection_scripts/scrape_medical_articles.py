#!/usr/bin/env python3
"""
Medical Article Scraper for TrustMed AI
Collects high-quality articles from trusted medical websites about diabetes and hypertension.
Implements rate limiting and anti-blocking measures to avoid getting blocked.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from medical_article_urls import MEDICAL_ARTICLE_URLS


class MedicalArticleScraper:
    """Scrapes medical articles from trusted health websites."""

    def __init__(self, output_dir='../data/auth_src/medical_articles'):
        self.output_dir = output_dir
        self.metadata_file = os.path.join(output_dir, 'articles_metadata.json')
        self.articles_collected = []

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Load existing metadata if available
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.articles_collected = json.load(f)

        # User agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

        # Search terms for diabetes and hypertension
        self.search_terms = {
            'diabetes': [
                'type 2 diabetes symptoms',
                'diabetes medications',
                'diabetes treatment',
                'diabetes lifestyle changes',
                'diabetes diagnosis',
                'diabetes management',
                'diabetes complications',
                'prediabetes',
                'insulin resistance',
                'blood sugar control',
            ],
            'hypertension': [
                'high blood pressure symptoms',
                'hypertension medications',
                'hypertension treatment',
                'blood pressure management',
                'hypertension diagnosis',
                'hypertension lifestyle',
                'reducing blood pressure',
                'hypertension complications',
                'blood pressure control',
                'antihypertensive drugs',
            ]
        }

        # Load comprehensive URL lists from external file
        self.trusted_sources = {}
        for source_name, urls in MEDICAL_ARTICLE_URLS.items():
            self.trusted_sources[source_name] = {
                'urls': urls,
                'base_url': self.extract_base_url(urls[0] if urls else ''),
            }

    def extract_base_url(self, url):
        """Extract base URL from a full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_random_headers(self):
        """Generate random headers to avoid detection."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def rate_limit(self, min_delay=1, max_delay=3):
        """Implement random delay to avoid rate limiting."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def sanitize_filename(self, text, max_length=100):
        """Create a safe filename from text."""
        # Remove special characters
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with underscores
        text = re.sub(r'[-\s]+', '_', text)
        # Truncate to max length
        return text[:max_length].strip('_')

    def extract_article_content(self, soup, source_name):
        """Extract article content from BeautifulSoup object."""
        content = []

        # Try to find the main article content
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')

        if not article:
            # Fallback: try to find content div
            article = soup.find('div', {'id': 'content'}) or soup.find('div', {'class': 'article-body'})

        if article:
            # Extract paragraphs
            paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
            for para in paragraphs:
                text = para.get_text(strip=True)
                if text and len(text) > 20:  # Only include substantial text
                    content.append(text)

        return '\n\n'.join(content)

    def scrape_article(self, url, source_name):
        """Scrape a single article from a URL."""
        try:
            print(f"\n  Fetching: {url}")
            headers = self.get_random_headers()

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = soup.find('h1')
            if title:
                title = title.get_text(strip=True)
            else:
                title = soup.title.get_text(strip=True) if soup.title else 'Untitled'

            # Extract article content
            content = self.extract_article_content(soup, source_name)

            if not content or len(content) < 500:
                print(f"  ⚠ Skipping - insufficient content (length: {len(content)})")
                return None

            # Create filename
            filename = f"{source_name.replace(' ', '_')}_{self.sanitize_filename(title)}.txt"
            filepath = os.path.join(self.output_dir, filename)

            # Check if already collected
            if any(article['filename'] == filename for article in self.articles_collected):
                print(f"  ℹ Already collected: {filename}")
                return None

            # Save article
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Source: {source_name}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Collected: {datetime.now().isoformat()}\n")
                f.write(f"\n{'=' * 80}\n\n")
                f.write(content)

            # Save metadata
            metadata = {
                'title': title,
                'source': source_name,
                'url': url,
                'filename': filename,
                'filepath': filepath,
                'word_count': len(content.split()),
                'collected_at': datetime.now().isoformat(),
            }

            self.articles_collected.append(metadata)
            self.save_metadata()

            print(f"  ✓ [{len(self.articles_collected)}] Saved: {filename} ({len(content.split())} words)")
            return metadata

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Error processing {url}: {e}")
            return None

    def save_metadata(self):
        """Save metadata to JSON file."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.articles_collected, f, indent=2)

    def find_related_links(self, soup, base_url, keywords):
        """Find related article links on a page."""
        links = []

        # Find all links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True).lower()

            # Check if link text contains relevant keywords
            if any(keyword.lower() in text for keyword in keywords):
                full_url = urljoin(base_url, href)

                # Only include links from the same domain
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if full_url not in links:
                        links.append(full_url)

        return links

    def scrape_source(self, source_name, config, max_articles=30):
        """Scrape articles from a single source."""
        print(f"\n{'=' * 80}")
        print(f"Scraping: {source_name}")
        print(f"{'=' * 80}")

        articles_scraped = 0
        urls_to_scrape = config['urls'].copy()
        visited_urls = set()

        # Shuffle URLs to get variety
        random.shuffle(urls_to_scrape)

        while urls_to_scrape and articles_scraped < max_articles:
            url = urls_to_scrape.pop(0)

            if url in visited_urls:
                continue

            visited_urls.add(url)

            # Scrape the article
            metadata = self.scrape_article(url, source_name)

            if metadata:
                articles_scraped += 1

            # Rate limiting
            self.rate_limit(min_delay=1, max_delay=2)

        print(f"\n{source_name}: Collected {articles_scraped} articles")
        return articles_scraped

    def scrape_all(self, target_count=200):
        """Scrape articles from all sources."""
        print(f"\nStarting Medical Article Scraper")
        print(f"Target: {target_count} articles")
        print(f"Already collected: {len(self.articles_collected)} articles")
        print(f"Output directory: {self.output_dir}")

        remaining = target_count - len(self.articles_collected)
        if remaining <= 0:
            print(f"\n✓ Target already reached!")
            return

        # Calculate articles per source
        articles_per_source = max(5, remaining // len(self.trusted_sources))

        print(f"\nTarget per source: ~{articles_per_source} articles")

        total_scraped = 0

        for source_name, config in self.trusted_sources.items():
            if len(self.articles_collected) >= target_count:
                print(f"\n✓ Target of {target_count} articles reached!")
                break

            scraped = self.scrape_source(source_name, config, max_articles=articles_per_source)
            total_scraped += scraped

            # Shorter delay between sources
            if len(self.articles_collected) < target_count:
                print(f"\n[Progress: {len(self.articles_collected)}/{target_count}] Pausing before next source...")
                time.sleep(random.uniform(3, 5))

        print(f"\n{'=' * 80}")
        print(f"SCRAPING COMPLETE")
        print(f"{'=' * 80}")
        print(f"Total articles collected this session: {total_scraped}")
        print(f"Total articles in database: {len(self.articles_collected)}")
        print(f"Output directory: {self.output_dir}")
        print(f"Metadata file: {self.metadata_file}")

        # Print summary by source
        print(f"\nBreakdown by source:")
        source_counts = {}
        for article in self.articles_collected:
            source = article['source']
            source_counts[source] = source_counts.get(source, 0) + 1

        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count} articles")


def main():
    """Main function."""
    # Create scraper instance
    scraper = MedicalArticleScraper(output_dir='../data/auth_src/medical_articles')

    # Scrape up to 200 articles
    scraper.scrape_all(target_count=200)


if __name__ == '__main__':
    main()
