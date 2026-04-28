"""Jora Australia job scraper."""

import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import quote, urljoin
import hashlib

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("jora_scraper")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class JoraScraper:
    """Scraper for Jora Australia."""
    
    def __init__(self):
        self.min_delay = 2
        
    def search(self, keywords: List[str], location: str) -> List[RawJob]:
        """Search Jora for jobs."""
        jobs = []
        keywords_str = "+".join(keywords)
        location_encoded = quote(location)
        
        search_url = f"https://au.jora.com/j?q={keywords_str}&l={location_encoded}"
        logger.info(f"Jora search URL: {search_url}")
        
        if not PLAYWRIGHT_AVAILABLE:
            return []
        
        raw_data = self._fetch_with_playwright(search_url)
        
        if raw_data is None:
            return jobs
        
        for item in raw_data:
            try:
                if not item.get("title"):
                    continue
                href = item.get("href") or ""
                source_job_id = item.get("jobId") or None
                if not source_job_id:
                    match = re.search(r'/job/([a-zA-Z0-9_-]+)', href)
                    if match:
                        source_job_id = match.group(1)
                if not source_job_id:
                    source_job_id = hashlib.md5(
                        f"{item.get('title','')}{item.get('company','')}".encode()
                    ).hexdigest()[:12]
                
                clean_href = href.split("?")[0] if href else ""
                jora_url = urljoin("https://au.jora.com", clean_href) if clean_href else "https://au.jora.com"
                
                jobs.append(RawJob(
                    source="jora",
                    source_job_id=source_job_id,
                    title=item["title"],
                    company=item.get("company") or "Unknown Company",
                    location=item.get("location"),
                    salary_text=item.get("salary_text"),
                    description=item.get("description"),
                    url=jora_url,
                ))
            except Exception as e:
                continue
        
        logger.info(f"Jora: found {len(jobs)} jobs")
        return jobs
    
    def _fetch_with_playwright(self, url: str):
        """Fetch using Playwright."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-AU",
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(4)
                
                jobs_data = page.evaluate("""
    () => {
        const results = [];
        const cards = Array.from(document.querySelectorAll('div[class*="job-card"]'));
        for (const card of cards) {
            const title = card.querySelector('h2.job-title')?.innerText?.trim();
            if (!title) continue;
            results.push({
                title: title,
                company: card.querySelector('span.job-company')?.innerText?.trim(),
                location: card.querySelector('a.job-location')?.innerText?.trim(),
                href: card.querySelector('a.job-link')?.getAttribute('href'),
            });
        }
        return results;
    }
""")
                context.close()
                browser.close()
                return jobs_data
        except Exception as e:
            logger.warning(f"Jora fetch failed: {e}")
            return None


# RawJob - same as in seek_scraper
class RawJob:
    def __init__(self, source, source_job_id, title, company, url, location=None, salary_text=None, description=None, posted_at=None):
        self.source = source
        self.source_job_id = source_job_id
        self.title = title
        self.company = company
        self.url = url
        self.location = location
        self.salary_text = salary_text
        self.description = description
        self.posted_at = posted_at