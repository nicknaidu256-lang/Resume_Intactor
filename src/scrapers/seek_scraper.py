"""SEEK Australia job scraper."""

import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from urllib.parse import quote, urljoin
import hashlib

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seek_scraper")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - install with: pip install playwright")

from bs4 import BeautifulSoup


class RawJob:
    """Raw job data from a scraper."""
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


class SeekScraper:
    """Scraper for SEEK Australia."""
    
    def __init__(self):
        self.min_delay = 3
        
    def search(self, keywords: List[str], location: str) -> List[RawJob]:
        """Search SEEK for jobs."""
        jobs = []
        keywords_str = ",".join(keywords)
        
        search_url = f"https://www.seek.com.au/jobs/in-Melbourne-VIC?keywords={keywords_str}"
        logger.info(f"SEEK search URL: {search_url}")
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, falling back to HTTP")
            return self._search_http(keywords, location)
        
        # Try Playwright
        raw_data = self._fetch_with_playwright(search_url)
        
        if raw_data is None:
            logger.warning("Playwright fetch failed, returning empty list")
            return jobs
            
        for item in raw_data:
            try:
                if not item.get("title"):
                    continue
                    
                source_job_id = item.get("jobId") or None
                href = item.get("href") or ""
                if not source_job_id:
                    match = re.search(r'/job/(\d+)', href)
                    if match:
                        source_job_id = match.group(1)
                if not source_job_id:
                    source_job_id = hashlib.md5(
                        f"{item.get('title','')}{item.get('company','')}".encode()
                    ).hexdigest()[:12]
                
                if href.startswith("http"):
                    url = href
                elif href:
                    url = urljoin("https://www.seek.com.au", href)
                else:
                    url = f"https://www.seek.com.au/job/{source_job_id}"
                
                jobs.append(RawJob(
                    source="seek",
                    source_job_id=source_job_id,
                    title=item["title"],
                    company=item.get("company") or "Unknown Company",
                    location=item.get("location"),
                    salary_text=item.get("salary"),
                    description=item.get("description"),
                    url=url,
                ))
            except Exception as e:
                logger.warning(f"Failed to process SEEK job record: {e}")
                continue
        
        logger.info(f"Found {len(jobs)} job cards on SEEK")
        return jobs
    
    def _fetch_with_playwright(self, url: str) -> Optional[List]:
        """Fetch SEEK using Playwright."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-AU",
                )
                page = context.new_page()
                page.set_default_timeout(30000)
                
                logger.info(f"Navigating to {url}")
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(4)
                
                jobs_data = page.evaluate("""
    () => {
        const results = [];
        const cards = Array.from(document.querySelectorAll('article[data-job-id]'));
        for (const card of cards) {
            const title = card.querySelector('h3')?.innerText?.trim();
            if (!title) continue;
            const company = card.querySelector('[data-automation="jobCompany"]')?.innerText?.trim() || 'Unknown';
            const location = card.querySelector('[data-automation="jobCardLocation"]')?.innerText?.trim();
            const jobId = card.getAttribute('data-job-id');
            const link = card.querySelector('a')?.getAttribute('href');
            results.push({ title, company, location, jobId, href: link });
        }
        return results;
    }
""")
                context.close()
                browser.close()
                return jobs_data
                
        except Exception as e:
            logger.warning(f"Playwright fetch failed: {e}")
            return None
    
    def _search_http(self, keywords: List[str], location: str) -> List[RawJob]:
        """Fallback HTTP search."""
        return []  # Keep simple for now