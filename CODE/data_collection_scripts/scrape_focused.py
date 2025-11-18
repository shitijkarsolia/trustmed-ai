#!/usr/bin/env python3
"""
Focused Medical Article Scraper - Mayo Clinic & Cleveland Clinic
Aggressively scrapes diabetes and hypertension articles
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote
import re


class FocusedScraper:
    """Aggressive scraper for Mayo Clinic and Cleveland Clinic."""

    def __init__(self, output_dir='../data/auth_src/medical_articles'):
        self.output_dir = output_dir
        self.metadata_file = os.path.join(output_dir, 'articles_metadata.json')
        self.articles_collected = []

        os.makedirs(output_dir, exist_ok=True)

        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.articles_collected = json.load(f)

        # User agent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        # Search terms for sitemap/directory scraping
        self.topics = ['diabetes', 'hypertension', 'blood-pressure', 'blood-sugar',
                       'type-2-diabetes', 'prediabetes', 'insulin', 'glucose',
                       'high-blood-pressure', 'medication', 'treatment']

    def sanitize_filename(self, text, max_length=100):
        """Create a safe filename."""
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text[:max_length].strip('_')

    def extract_text(self, soup):
        """Extract clean text from BeautifulSoup."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text

    def scrape_mayo_clinic(self, max_articles=100):
        """Scrape Mayo Clinic articles."""
        print(f"\n{'='*80}")
        print("SCRAPING MAYO CLINIC")
        print(f"{'='*80}")

        articles_found = 0
        base_url = "https://www.mayoclinic.org"

        # Mayo Clinic article patterns
        search_paths = [
            "/diseases-conditions/diabetes",
            "/diseases-conditions/type-2-diabetes",
            "/diseases-conditions/high-blood-pressure",
            "/diseases-conditions/prediabetes",
            "/diseases-conditions/diabetes/in-depth",
            "/diseases-conditions/high-blood-pressure/in-depth",
        ]

        for path in search_paths:
            if articles_found >= max_articles:
                break

            try:
                url = base_url + path
                print(f"\nExploring: {url}")
                response = requests.get(url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find all article links
                links = soup.find_all('a', href=True)
                article_urls = set()

                for link in links:
                    href = link['href']
                    if any(topic in href.lower() for topic in self.topics):
                        if href.startswith('/'):
                            full_url = base_url + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue

                        if 'mayoclinic.org' in full_url:
                            article_urls.add(full_url)

                print(f"Found {len(article_urls)} potential articles")

                # Scrape each article
                for article_url in list(article_urls)[:30]:  # Limit per path
                    if articles_found >= max_articles:
                        break

                    if self.scrape_article(article_url, "Mayo Clinic"):
                        articles_found += 1
                        print(f"  [{len(self.articles_collected)}] Mayo Clinic articles collected")

                    time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"Error exploring {path}: {e}")
                continue

        return articles_found

    def scrape_cleveland_clinic(self, max_articles=100):
        """Scrape Cleveland Clinic articles."""
        print(f"\n{'='*80}")
        print("SCRAPING CLEVELAND CLINIC")
        print(f"{'='*80}")

        articles_found = 0
        base_url = "https://my.clevelandclinic.org"

        # Try different URL patterns
        url_patterns = [
            "https://my.clevelandclinic.org/health/diseases/{id}-{topic}",
        ]

        # Known working IDs (from previous successful scrapes)
        topics_with_ids = [
            ("diabetes", ["diabetes", "type-2-diabetes", "prediabetes", "diabetic"]),
            ("hypertension", ["high-blood-pressure", "hypertension", "blood-pressure"]),
        ]

        # Try search functionality
        search_urls = [
            "https://my.clevelandclinic.org/search?q=diabetes",
            "https://my.clevelandclinic.org/search?q=type+2+diabetes",
            "https://my.clevelandclinic.org/search?q=hypertension",
            "https://my.clevelandclinic.org/search?q=high+blood+pressure",
        ]

        for search_url in search_urls:
            if articles_found >= max_articles:
                break

            try:
                print(f"\nSearching: {search_url}")
                response = requests.get(search_url, headers=self.headers, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find article links
                links = soup.find_all('a', href=True)
                article_urls = set()

                for link in links:
                    href = link['href']
                    if '/health/' in href:
                        if href.startswith('/'):
                            full_url = base_url + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue

                        if 'clevelandclinic.org' in full_url:
                            article_urls.add(full_url)

                print(f"Found {len(article_urls)} potential articles")

                # Scrape each article
                for article_url in list(article_urls)[:30]:
                    if articles_found >= max_articles:
                        break

                    if self.scrape_article(article_url, "Cleveland Clinic"):
                        articles_found += 1
                        print(f"  [{len(self.articles_collected)}] Cleveland Clinic articles collected")

                    time.sleep(random.uniform(0.5, 1.5))

            except Exception as e:
                print(f"Error searching: {e}")
                continue

        return articles_found

    def scrape_article(self, url, source_name):
        """Scrape a single article."""
        try:
            # Check if already collected
            if any(article['url'] == url for article in self.articles_collected):
                return False

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

            # Extract content
            content = self.extract_text(soup)

            if len(content) < 500:
                return False

            # Create filename
            filename = f"{source_name.replace(' ', '_')}_{self.sanitize_filename(title)}.txt"
            filepath = os.path.join(self.output_dir, filename)

            # Check if filename exists
            if any(article['filename'] == filename for article in self.articles_collected):
                return False

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

            return True

        except Exception as e:
            return False

    def save_metadata(self):
        """Save metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.articles_collected, f, indent=2)

    def run(self, target=200):
        """Run the scraper."""
        print(f"\nFOCUSED SCRAPER - Mayo Clinic & Cleveland Clinic")
        print(f"Current: {len(self.articles_collected)} articles")
        print(f"Target: {target} articles")

        # Scrape Mayo Clinic
        mayo_target = (target - len(self.articles_collected)) // 2
        mayo_collected = self.scrape_mayo_clinic(max_articles=mayo_target)

        # Scrape Cleveland Clinic
        cleveland_target = target - len(self.articles_collected)
        cleveland_collected = self.scrape_cleveland_clinic(max_articles=cleveland_target)

        print(f"\n{'='*80}")
        print("SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"Total articles: {len(self.articles_collected)}")
        print(f"Mayo Clinic: {mayo_collected} new")
        print(f"Cleveland Clinic: {cleveland_collected} new")


if __name__ == '__main__':
    scraper = FocusedScraper()
    scraper.run(target=200)
