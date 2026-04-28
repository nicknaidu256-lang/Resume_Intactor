"""Jora Australia job scraper for AU Job Application Pipeline."""

import re
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote, urljoin
import hashlib

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, RawJob
from src.config import config
from src.utils import get_logger


class JoraScraper(BaseScraper):
    """Scraper for Jora Australia (au.jora.com)."""

    def __init__(self):
        super().__init__(name="jora", min_delay_seconds=2)
        self.logger = get_logger("scraper.jora")

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        """Search Jora for jobs."""
        jobs = []
        keywords_str = "+".join(keywords)
        location_encoded = quote(location)
        
        search_url = f"https://au.jora.com/j?q={keywords_str}&l={location_encoded}"
        
        self.logger.info(f"Jora search URL: {search_url}")
        
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright not available, falling back to HTTP")
            return self._search_http(keywords, location)
        
        raw_data = self._fetch_with_playwright(search_url)
        
        if raw_data is None:
            self.logger.warning("Jora Playwright fetch failed, returning empty list")
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
                
                posted_at = self._parse_posted_date(item.get("listed") or "")
                
                jobs.append(RawJob(
                    source="jora",
                    source_job_id=source_job_id,
                    title=item["title"],
                    company=item.get("company") or "Unknown Company",
                    location=item.get("location"),
                    salary_text=item.get("salary_text"),
                    description=item.get("description"),
                    url=jora_url,
                    posted_at=posted_at,
                ))
            except Exception as e:
                self.logger.warning(f"Failed to process Jora job record: {e}")
                continue
        
        self.logger.info(f"Parsed {len(jobs)} jobs from Jora")
        return jobs

    def _fetch_with_playwright(self, url: str) -> Optional[list]:
        """Fetch URL using Playwright headless browser."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-AU",
                    timezone_id="Australia/Melbourne",
                )
                page = context.new_page()
                
                page.set_default_timeout(30000)
                
                self.logger.info(f"Navigating to {url}")
                page.goto(url, wait_until="domcontentloaded")
                
                try:
                    page.wait_for_selector("article.result-card, div[data-testid='job-card'], div.job-result", timeout=10000)
                except Exception:
                    pass
                
                time.sleep(6)
                
                page_content = page.content()
                
                if "captcha" in page_content.lower() or "blocked" in page_content.lower() or "just a moment" in page_content.lower():
                    self.logger.warning("Jora blocked or CAPTCHA detected")
                    context.close()
                    browser.close()
                    return None
                
                jobs_data = page.evaluate("""
    () => {
        const results = [];
        const cards = Array.from(document.querySelectorAll('div[class*="job-card"]'));

        for (const card of cards) {
            const titleEl   = card.querySelector('h2.job-title');
            const companyEl = card.querySelector('span.job-company');
            const locationEl= card.querySelector('a.job-location');
            const salaryEl  = card.querySelector('[class*="salary"], [class*="pay"]');
            const summaryEl = card.querySelector('div.job-abstract, ul');
            const dateEl    = card.querySelector('span.job-listed-date');
            const linkEl    = card.querySelector('a.job-link.-no-underline.-desktop-only, a.job-link');
            const saveBtn   = card.querySelector('button[data-job-id]');

            const title = titleEl ? titleEl.innerText.trim() : null;
            if (!title) continue;

            results.push({
                title,
                company:  companyEl  ? companyEl.innerText.trim()  : null,
                location: locationEl ? locationEl.innerText.trim() : null,
                salary_text: salaryEl ? salaryEl.innerText.trim()  : null,
                description: summaryEl ? summaryEl.innerText.trim() : null,
                listed:   dateEl    ? dateEl.innerText.trim()     : null,
                href:     linkEl    ? linkEl.getAttribute('href') : null,
                jobId:    saveBtn   ? saveBtn.getAttribute('data-job-id') : null,
            });
        }
        return results;
    }
""")

                self.logger.info(f"Extracted {len(jobs_data)} job records via Playwright JS")

                context.close()
                browser.close()
                return jobs_data

        except ImportError:
            self.logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            self.logger.warning(f"Playwright fetch failed: {e}")
            return None

    def _search_http(self, keywords: list[str], location: str) -> list[RawJob]:
        """Fallback HTTP-based search if Playwright unavailable."""
        jobs = []
        keywords_str = "+".join(keywords)
        location_encoded = quote(location)
        
        search_url = f"https://au.jora.com/j?q={keywords_str}&l={location_encoded}"
        
        self.logger.info(f"Jora search URL (HTTP fallback): {search_url}")
        
        response = self._request_with_retry(search_url, max_retries=1)
        
        if response is None:
            self.logger.warning("Jora request failed, returning empty list")
            return jobs
        
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            
            job_cards = soup.select("div.job-card")
            
            if not job_cards:
                job_cards = soup.select("article.result-card")
            
            if not job_cards:
                job_cards = soup.select("div[data-test='job-card']")
            
            if not job_cards:
                job_cards = soup.select("a.job-result-card")
            
            self.logger.info(f"Found {len(job_cards)} job cards on Jora")
            
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Failed to parse job card: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to parse Jora response: {e}")
            
        return jobs

    def _parse_job_card(self, card) -> Optional[RawJob]:
        """Parse a single job card from Jora."""
        try:
            source_job_id = None
            if card.get("data-id"):
                source_job_id = str(card.get("data-id"))
            
            if not source_job_id:
                link_elem = card.select_one("a")
                if link_elem and link_elem.get("href"):
                    match = re.search(r'/job/(\d+)', link_elem.get("href", ""))
                    if match:
                        source_job_id = match.group(1)
            
            if not source_job_id:
                url = None
                link_elem = card.select_one("a")
                if link_elem and link_elem.get("href"):
                    href = link_elem.get("href", "")
                    if "/job/" in href:
                        match = re.search(r'/job/([a-zA-Z0-9_-]+)', href)
                        if match:
                            source_job_id = match.group(1)
                            clean_href = href.split("?")[0]
                            url = urljoin("https://au.jora.com", clean_href)
            
            if not source_job_id:
                self.logger.debug("Could not extract job ID, skipping")
                return None
            
            title = None
            title_elem = card.select_one("h3") or card.select_one("a.title")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if not title:
                self.logger.debug("Could not extract job title, skipping")
                return None
            
            company = None
            company_elem = card.select_one("span.company") or card.select_one("div.company")
            if company_elem:
                company = company_elem.get_text(strip=True)
            
            if not company:
                company = "Unknown Company"
            
            location = None
            location_elem = card.select_one("span.location") or card.select_one("div.location")
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            salary_text = None
            salary_elem = card.select_one("span.salary") or card.select_one("div.salary")
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
            
            description = None
            desc_elem = card.select_one("p.summary") or card.select_one("div.summary")
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            url = None
            link_elem = card.select_one("a")
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href", "")
                clean_href = href.split("?")[0]
                if href.startswith("http"):
                    url = clean_href
                else:
                    url = urljoin("https://au.jora.com", clean_href)
            
            if not url:
                url = f"https://au.jora.com/job/{source_job_id}"
            
            posted_at = None
            posted_elem = card.select_one("span.time") or card.select_one("div.posted")
            if posted_elem:
                posted_text = posted_elem.get_text(strip=True)
                posted_at = self._parse_posted_date(posted_text)
            
            return RawJob(
                source="jora",
                source_job_id=source_job_id,
                title=title,
                company=company,
                location=location,
                salary_text=salary_text,
                description=description,
                url=url,
                posted_at=posted_at,
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing job card: {e}")
            return None

    def _parse_posted_date(self, date_text: str) -> Optional[str]:
        """Parse Jora's relative date format."""
        if not date_text:
            return None
            
        date_text = date_text.lower().strip()
        
        now = datetime.now()
        
        if "just now" in date_text or "today" in date_text:
            return now.strftime("%Y-%m-%d")
        
        if "hour" in date_text:
            match = re.search(r'(\d+)', date_text)
            if match:
                return now.strftime("%Y-%m-%d")
        
        if "minute" in date_text:
            return now.strftime("%Y-%m-%d")
        
        match = re.search(r'(\d+)\s*day', date_text)
        if match:
            days = int(match.group(1))
            date_obj = now - timedelta(days=days)
            return date_obj.strftime("%Y-%m-%d")
        
        match = re.search(r'(\d+)\s*week', date_text)
        if match:
            weeks = int(match.group(1))
            date_obj = now - timedelta(weeks=weeks)
            return date_obj.strftime("%Y-%m-%d")
        
        match = re.search(r'(\d+)\s*month', date_text)
        if match:
            months = int(match.group(1))
            date_obj = now - timedelta(days=months * 30)
            return date_obj.strftime("%Y-%m-%d")
        
        return None