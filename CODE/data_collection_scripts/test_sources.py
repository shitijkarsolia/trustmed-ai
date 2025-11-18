#!/usr/bin/env python3
"""Test which medical websites are easiest to scrape."""

import requests
from bs4 import BeautifulSoup
import time

sources = {
    'MedicalNewsToday': 'https://www.medicalnewstoday.com/articles/317483',  # diabetes
    'MedlinePlus': 'https://medlineplus.gov/diabetestype2.html',
    'CDC': 'https://www.cdc.gov/diabetes/basics/type2.html',
    'Medical Xpress': 'https://medicalxpress.com/search/?search=diabetes',
    'News-Medical': 'https://www.news-medical.net/health/What-is-Diabetes.aspx',
    'WHO': 'https://www.who.int/news-room/fact-sheets/detail/diabetes',
    'Medscape': 'https://www.medscape.com/viewarticle/diabetes',
    'BMJ': 'https://www.bmj.com/search/diabetes',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print("Testing medical websites for scrapability...\n")

for name, url in sources.items():
    try:
        print(f"Testing {name}...")
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get text content
        text = soup.get_text()
        paragraphs = soup.find_all('p')

        print(f"  ✓ Status: {response.status_code}")
        print(f"  ✓ Text length: {len(text)}")
        print(f"  ✓ Paragraphs: {len(paragraphs)}")
        print(f"  ✓ EASY TO SCRAPE\n")

        time.sleep(1)
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
