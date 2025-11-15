#!/usr/bin/env python3
"""
Deep scraper - explores more article IDs and search results.
Goal: Reach 150-200 articles on diabetes and hypertension.
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


class DeepScraper:
    """Deep scraper for medical articles."""

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

    def sanitize_filename(self, text, max_length=100):
        """Create safe filename."""
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text[:max_length].strip('_')

    def extract_clean_text(self, soup):
        """Extract clean article text."""
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article'))

        if article:
            paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'li'])
        else:
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])

        text_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 20:
                text_parts.append(text)

        return '\n\n'.join(text_parts)

    def scrape_article(self, url, source_name):
        """Scrape single article."""
        try:
            if any(a['url'] == url for a in self.articles_collected):
                return False

            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return False

            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else 'Untitled'

            content = self.extract_clean_text(soup)

            if len(content) < 500:
                return False

            filename = f"{source_name.replace(' ', '_')}_{self.sanitize_filename(title)}.txt"
            filepath = os.path.join(self.output_dir, filename)

            if any(a['filename'] == filename for a in self.articles_collected):
                return False

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Source: {source_name}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Collected: {datetime.now().isoformat()}\n\n")
                f.write(f"{'='*80}\n\n")
                f.write(content)

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

    def scrape_medical_news_today_deep(self, max_articles=50):
        """Deep scrape of MedicalNewsToday using article ID ranges."""
        print(f"\n{'='*80}\nDEEP SCRAPING: MedicalNewsToday\n{'='*80}")

        base_url = 'https://www.medicalnewstoday.com'

        # Expanded list of article IDs related to diabetes/hypertension
        article_ids = [
            # Diabetes articles
            '317483', '323627', '323733', '318472', '323013', '305010',
            '161285', '323080', '315409', '316889', '323825', '305011',
            '323074', '305098', '305062', '323741', '323456', '323159',
            '305075', '323892', '320941', '323654', '305023', '317535',
            '323784', '305042', '323623', '305086', '323741', '305091',
            # Hypertension articles
            '150109', '322284', '322185', '271763', '320051', '320124',
            '318652', '323682', '322266', '159283', '322298', '271847',
            '322354', '322418', '322156', '271895', '322493', '159046',
            '322537', '322621', '271923', '322689', '322753', '322812',
            # Related health topics
            '321456', '321523', '321598', '321672', '321745', '321812',
            '321889', '321956', '322023', '322089', '322156', '322223',
        ]

        count = 0
        for article_id in article_ids:
            if count >= max_articles:
                break
            url = f"{base_url}/articles/{article_id}"
            if self.scrape_article(url, "MedicalNewsToday"):
                count += 1
            time.sleep(random.uniform(0.3, 0.8))

        print(f"MedicalNewsToday Deep: Collected {count} articles")
        return count

    def scrape_news_medical_deep(self, max_articles=50):
        """Deep scrape of News-Medical."""
        print(f"\n{'='*80}\nDEEP SCRAPING: News-Medical\n{'='*80}")

        base_url = 'https://www.news-medical.net'

        # Comprehensive list of health topics
        health_topics = [
            '/health/What-is-Diabetes.aspx',
            '/health/Type-2-Diabetes.aspx',
            '/health/Type-1-Diabetes.aspx',
            '/health/Diabetes-Symptoms.aspx',
            '/health/Diabetes-Diagnosis.aspx',
            '/health/Diabetes-Treatment.aspx',
            '/health/Diabetes-Medication.aspx',
            '/health/Diabetes-Diet.aspx',
            '/health/Diabetes-Complications.aspx',
            '/health/Diabetes-Management.aspx',
            '/health/What-is-Hypertension.aspx',
            '/health/Hypertension-Symptoms.aspx',
            '/health/Hypertension-Diagnosis.aspx',
            '/health/Hypertension-Treatment.aspx',
            '/health/Hypertension-Causes.aspx',
            '/health/Blood-Pressure-Medication.aspx',
            '/health/High-Blood-Pressure.aspx',
            '/health/What-is-Prediabetes.aspx',
            '/health/Insulin-Therapy.aspx',
            '/health/Insulin-Resistance.aspx',
            '/health/Metformin.aspx',
            '/health/ACE-Inhibitors.aspx',
            '/health/Beta-Blockers.aspx',
            '/health/Calcium-Channel-Blockers.aspx',
            '/health/Diuretics.aspx',
            '/health/Blood-Glucose.aspx',
            '/health/Glycemic-Control.aspx',
            '/health/HbA1c.aspx',
            '/health/Cardiovascular-Disease.aspx',
            '/health/Heart-Health.aspx',
        ]

        count = 0
        for path in health_topics:
            if count >= max_articles:
                break
            url = base_url + path
            if self.scrape_article(url, "News-Medical"):
                count += 1
            time.sleep(random.uniform(0.3, 0.8))

        print(f"News-Medical Deep: Collected {count} articles")
        return count

    def scrape_medical_xpress_deep(self, max_articles=40):
        """Deep scrape of Medical Xpress."""
        print(f"\n{'='*80}\nDEEP SCRAPING: Medical Xpress\n{'='*80}")

        base_url = 'https://medicalxpress.com'

        # Expanded search terms
        search_terms = [
            'diabetes', 'type-2-diabetes', 'type-1-diabetes',
            'diabetes-treatment', 'diabetes-medication', 'insulin',
            'blood-sugar', 'glucose', 'metformin', 'a1c',
            'hypertension', 'high-blood-pressure', 'blood-pressure',
            'blood-pressure-medication', 'ace-inhibitor', 'beta-blocker',
            'cardiovascular', 'heart-health', 'prediabetes',
        ]

        count = 0
        for term in search_terms:
            if count >= max_articles:
                break
            try:
                url = f"{base_url}/search/?search={term}&s=1"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                for link in soup.find_all('a', href=True):
                    if count >= max_articles:
                        break
                    href = link['href']
                    if '/news/' in href and 'medicalxpress.com' in href:
                        if self.scrape_article(href, "Medical Xpress"):
                            count += 1
                        time.sleep(random.uniform(0.3, 0.8))

                time.sleep(1)
            except:
                continue

        print(f"Medical Xpress Deep: Collected {count} articles")
        return count

    def scrape_medlineplus_deep(self, max_articles=30):
        """Deep scrape of MedlinePlus."""
        print(f"\n{'='*80}\nDEEP SCRAPING: MedlinePlus\n{'='*80}")

        urls = [
            'https://medlineplus.gov/diabetestype2.html',
            'https://medlineplus.gov/diabetes.html',
            'https://medlineplus.gov/diabetestype1.html',
            'https://medlineplus.gov/diabetesmedicines.html',
            'https://medlineplus.gov/diabetesdiet.html',
            'https://medlineplus.gov/diabetesandpregnancy.html',
            'https://medlineplus.gov/diabetesinchildrenandteens.html',
            'https://medlineplus.gov/prediabetes.html',
            'https://medlineplus.gov/highbloodpressure.html',
            'https://medlineplus.gov/highbloodpressuremedicines.html',
            'https://medlineplus.gov/howtopreventhighbloodpressure.html',
            'https://medlineplus.gov/bloodpressure.html',
            'https://medlineplus.gov/diabetescomplications.html',
            'https://medlineplus.gov/kidneydiseases.html',
            'https://medlineplus.gov/heartdiseases.html',
            'https://medlineplus.gov/bloodsugar.html',
            'https://medlineplus.gov/a1c.html',
            'https://medlineplus.gov/insulin.html',
        ]

        count = 0
        for url in urls:
            if count >= max_articles:
                break
            if self.scrape_article(url, "MedlinePlus"):
                count += 1
            time.sleep(random.uniform(0.3, 0.8))

        print(f"MedlinePlus Deep: Collected {count} articles")
        return count

    def run(self, target=200):
        """Run deep scraper."""
        print(f"\n{'='*80}")
        print(f"DEEP SCRAPER")
        print(f"Current: {len(self.articles_collected)} articles")
        print(f"Target: {target} articles")
        print(f"{'='*80}")

        start_count = len(self.articles_collected)

        # Deep scrape all sources
        self.scrape_medical_news_today_deep(max_articles=80)
        if len(self.articles_collected) >= target:
            self.print_summary(start_count)
            return

        self.scrape_news_medical_deep(max_articles=60)
        if len(self.articles_collected) >= target:
            self.print_summary(start_count)
            return

        self.scrape_medical_xpress_deep(max_articles=50)
        if len(self.articles_collected) >= target:
            self.print_summary(start_count)
            return

        self.scrape_medlineplus_deep(max_articles=40)

        self.print_summary(start_count)

    def print_summary(self, start_count):
        """Print summary."""
        print(f"\n{'='*80}")
        print(f"DEEP SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"New articles: {len(self.articles_collected) - start_count}")
        print(f"Total articles: {len(self.articles_collected)}")


if __name__ == '__main__':
    scraper = DeepScraper()
    scraper.run(target=200)
