#!/usr/bin/env python3
"""
Aggressive scraper for easy-to-scrape medical websites.
Focus: diabetes, hypertension symptoms, medications, lifestyle, diagnosis
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse


class EasyScraper:
    """Scrapes easy medical websites."""

    def __init__(self, output_dir='../data/medical_articles'):
        self.output_dir = output_dir
        self.metadata_file = os.path.join(output_dir, 'articles_metadata.json')
        self.articles_collected = []

        os.makedirs(output_dir, exist_ok=True)

        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.articles_collected = json.load(f)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        # Topics to search for
        self.diabetes_topics = [
            'type-2-diabetes', 'diabetes-symptoms', 'diabetes-treatment',
            'diabetes-medication', 'diabetes-diet', 'diabetes-diagnosis',
            'prediabetes', 'insulin', 'blood-sugar', 'glucose', 'a1c',
            'metformin', 'diabetic-complications', 'diabetes-lifestyle'
        ]

        self.hypertension_topics = [
            'high-blood-pressure', 'hypertension', 'blood-pressure-treatment',
            'blood-pressure-medication', 'blood-pressure-diet',
            'ace-inhibitors', 'beta-blockers', 'diuretics', 'dash-diet',
            'hypertension-symptoms', 'hypertension-diagnosis'
        ]

    def sanitize_filename(self, text, max_length=100):
        """Create safe filename."""
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text[:max_length].strip('_')

    def extract_clean_text(self, soup):
        """Extract clean article text."""
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        # Try to find main content
        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article'))

        if article:
            paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'li'])
        else:
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])

        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:  # Only substantial text
                text_parts.append(text)

        return '\n\n'.join(text_parts)

    def scrape_article(self, url, source_name):
        """Scrape single article."""
        try:
            # Check if already collected
            if any(a['url'] == url for a in self.articles_collected):
                return False

            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return False

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

            # Extract content
            content = self.extract_clean_text(soup)

            if len(content) < 500:
                return False

            # Create filename
            filename = f"{source_name.replace(' ', '_')}_{self.sanitize_filename(title)}.txt"
            filepath = os.path.join(self.output_dir, filename)

            if any(a['filename'] == filename for a in self.articles_collected):
                return False

            # Save article
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Source: {source_name}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Collected: {datetime.now().isoformat()}\n\n")
                f.write(f"{'='*80}\n\n")
                f.write(content)

            # Save metadata
            self.articles_collected.append({
                'title': title,
                'source': source_name,
                'url': url,
                'filename': filename,
                'filepath': filepath,
                'word_count': len(content.split()),
                'collected_at': datetime.now().isoformat(),
            })

            self.save_metadata()
            print(f"  [{len(self.articles_collected)}] ✓ {title[:60]}...")
            return True

        except Exception as e:
            return False

    def save_metadata(self):
        """Save metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.articles_collected, f, indent=2)

    def scrape_medical_news_today(self, max_articles=50):
        """Scrape MedicalNewsToday."""
        print(f"\n{'='*80}\nSCRAPING: MedicalNewsToday\n{'='*80}")

        base_url = 'https://www.medicalnewstoday.com'
        article_ids = {
            # Diabetes
            '317483': 'type-2-diabetes',
            '323627': 'diabetes-treatment',
            '323733': 'diabetes-symptoms',
            '318472': 'diabetes-medications',
            '323013': 'diabetes-diet',
            '305010': 'prediabetes',
            '161285': 'insulin',
            '323080': 'metformin',
            '315409': 'blood-sugar-levels',
            # Hypertension
            '150109': 'high-blood-pressure',
            '322284': 'blood-pressure-chart',
            '322185': 'blood-pressure-medication',
            '271763': 'ace-inhibitors',
            '320051': 'beta-blockers',
            '320124': 'diuretics',
            '318652': 'dash-diet',
            '323682': 'hypertension-symptoms',
        }

        count = 0
        for article_id, topic in article_ids.items():
            if count >= max_articles:
                break
            url = f"{base_url}/articles/{article_id}"
            if self.scrape_article(url, "MedicalNewsToday"):
                count += 1
            time.sleep(random.uniform(0.5, 1.5))

        # Try to find more articles via search
        search_terms = ['type-2-diabetes', 'hypertension', 'blood-pressure-medication',
                        'diabetes-symptoms', 'diabetes-medication']

        for term in search_terms:
            if count >= max_articles:
                break
            try:
                url = f"{base_url}/search?q={term}"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find article links
                for link in soup.find_all('a', href=True):
                    if count >= max_articles:
                        break
                    href = link['href']
                    if '/articles/' in href and href.count('/') >= 2:
                        full_url = urljoin(base_url, href)
                        if self.scrape_article(full_url, "MedicalNewsToday"):
                            count += 1
                        time.sleep(random.uniform(0.5, 1.5))

                time.sleep(2)
            except:
                continue

        print(f"MedicalNewsToday: Collected {count} articles")
        return count

    def scrape_news_medical(self, max_articles=50):
        """Scrape News-Medical.net."""
        print(f"\n{'='*80}\nSCRAPING: News-Medical\n{'='*80}")

        base_url = 'https://www.news-medical.net'

        # Known good URLs
        urls = [
            '/health/What-is-Diabetes.aspx',
            '/health/Type-2-Diabetes.aspx',
            '/health/Diabetes-Symptoms.aspx',
            '/health/Diabetes-Treatment.aspx',
            '/health/Diabetes-Medication.aspx',
            '/health/What-is-Hypertension.aspx',
            '/health/Hypertension-Symptoms.aspx',
            '/health/Hypertension-Treatment.aspx',
            '/health/Blood-Pressure-Medication.aspx',
            '/health/What-is-Prediabetes.aspx',
            '/health/Insulin-Therapy.aspx',
            '/health/ACE-Inhibitors.aspx',
            '/health/Beta-Blockers.aspx',
        ]

        count = 0
        for path in urls:
            if count >= max_articles:
                break
            url = base_url + path
            if self.scrape_article(url, "News-Medical"):
                count += 1
            time.sleep(random.uniform(0.5, 1.5))

        # Try search
        for topic in ['diabetes', 'hypertension', 'blood pressure']:
            if count >= max_articles:
                break
            try:
                search_url = f"{base_url}/medical/search?query={topic}"
                response = requests.get(search_url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                for link in soup.find_all('a', href=True):
                    if count >= max_articles:
                        break
                    href = link['href']
                    if '/health/' in href and href.endswith('.aspx'):
                        full_url = urljoin(base_url, href)
                        if self.scrape_article(full_url, "News-Medical"):
                            count += 1
                        time.sleep(random.uniform(0.5, 1.5))

                time.sleep(2)
            except:
                continue

        print(f"News-Medical: Collected {count} articles")
        return count

    def scrape_who(self, max_articles=20):
        """Scrape WHO."""
        print(f"\n{'='*80}\nSCRAPING: WHO\n{'='*80}")

        urls = [
            'https://www.who.int/news-room/fact-sheets/detail/diabetes',
            'https://www.who.int/news-room/fact-sheets/detail/hypertension',
            'https://www.who.int/health-topics/diabetes',
            'https://www.who.int/health-topics/hypertension',
        ]

        count = 0
        for url in urls:
            if count >= max_articles:
                break
            if self.scrape_article(url, "WHO"):
                count += 1
            time.sleep(random.uniform(1, 2))

        print(f"WHO: Collected {count} articles")
        return count

    def scrape_medlineplus(self, max_articles=30):
        """Scrape MedlinePlus."""
        print(f"\n{'='*80}\nSCRAPING: MedlinePlus\n{'='*80}")

        urls = [
            'https://medlineplus.gov/diabetestype2.html',
            'https://medlineplus.gov/diabetes.html',
            'https://medlineplus.gov/diabetesmedicines.html',
            'https://medlineplus.gov/diabetesdiet.html',
            'https://medlineplus.gov/prediabetes.html',
            'https://medlineplus.gov/highbloodpressure.html',
            'https://medlineplus.gov/highbloodpressuremedicines.html',
            'https://medlineplus.gov/howtopreventhighbloodpressure.html',
            'https://medlineplus.gov/bloodpressure.html',
            'https://medlineplus.gov/diabetescomplications.html',
        ]

        count = 0
        for url in urls:
            if count >= max_articles:
                break
            if self.scrape_article(url, "MedlinePlus"):
                count += 1
            time.sleep(random.uniform(0.5, 1.5))

        print(f"MedlinePlus: Collected {count} articles")
        return count

    def scrape_medical_xpress(self, max_articles=30):
        """Scrape Medical Xpress."""
        print(f"\n{'='*80}\nSCRAPING: Medical Xpress\n{'='*80}")

        base_url = 'https://medicalxpress.com'

        # Try search results
        search_terms = ['type-2-diabetes', 'diabetes-treatment', 'hypertension',
                        'blood-pressure', 'diabetes-medication']

        count = 0
        for term in search_terms:
            if count >= max_articles:
                break
            try:
                url = f"{base_url}/search/?search={term}&s=1"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find article links
                for link in soup.find_all('a', href=True):
                    if count >= max_articles:
                        break
                    href = link['href']
                    if '/news/' in href and 'medicalxpress.com' in href:
                        if self.scrape_article(href, "Medical Xpress"):
                            count += 1
                        time.sleep(random.uniform(0.5, 1.5))

                time.sleep(2)
            except:
                continue

        print(f"Medical Xpress: Collected {count} articles")
        return count

    def run(self, target=200):
        """Run scraper."""
        print(f"\n{'='*80}")
        print(f"EASY SOURCE SCRAPER")
        print(f"Current: {len(self.articles_collected)} articles")
        print(f"Target: {target} articles")
        print(f"{'='*80}")

        start_count = len(self.articles_collected)

        # Scrape from easiest sources first
        self.scrape_medical_news_today(max_articles=60)
        if len(self.articles_collected) >= target:
            return

        self.scrape_news_medical(max_articles=50)
        if len(self.articles_collected) >= target:
            return

        self.scrape_medlineplus(max_articles=30)
        if len(self.articles_collected) >= target:
            return

        self.scrape_who(max_articles=20)
        if len(self.articles_collected) >= target:
            return

        self.scrape_medical_xpress(max_articles=40)

        print(f"\n{'='*80}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"New articles: {len(self.articles_collected) - start_count}")
        print(f"Total articles: {len(self.articles_collected)}")


if __name__ == '__main__':
    scraper = EasyScraper()
    scraper.run(target=200)
