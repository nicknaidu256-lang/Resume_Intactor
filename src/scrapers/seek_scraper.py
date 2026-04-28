"""SEEK Australia job scraper for AU Job Application Pipeline."""

import re
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import quote, urljoin
import hashlib

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, RawJob
from src.config import config
from src.utils import get_logger


class SeekScraper(BaseScraper):
    """Scraper for SEEK Australia (seek.com.au)."""

    def __init__(self):
        super().__init__(name="seek", min_delay_seconds=3)
        self.logger = get_logger("scraper.seek")

    def search(self, keywords: list[str], location: str) -> list[RawJob]:
        """Search SEEK for jobs."""
        jobs = []
        keywords_str = ",".join(keywords)
        location_encoded = quote(location)

        search_url = f"https://www.seek.com.au/jobs/in-Melbourne-VIC?keywords={keywords_str}"
        self.logger.info(f"SEEK search URL: {search_url}")

        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright not available, falling back to HTTP")
            return self._search_http(keywords, location)

        raw_data = self._fetch_with_playwright(search_url)

        if raw_data is None:
            self.logger.warning("Playwright fetch failed, returning empty list")
            return jobs

        for item in raw_data:
            try:
                if not item.get("title"):
                    continue

                # Job ID
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

                # URL
                if href.startswith("http"):
                    url = href
                elif href:
                    url = urljoin("https://www.seek.com.au", href)
                else:
                    url = f"https://www.seek.com.au/job/{source_job_id}"

                # Posted date
                posted_at = self._parse_posted_date(item.get("listed") or "")

                jobs.append(RawJob(
                    source="seek",
                    source_job_id=source_job_id,
                    title=item["title"],
                    company=item.get("company") or "Unknown Company",
                    location=item.get("location"),
                    salary_text=item.get("salary"),
                    description=item.get("description"),
                    url=url,
                    posted_at=posted_at,
                ))
            except Exception as e:
                self.logger.warning(f"Failed to process SEEK job record: {e}")
                continue

        self.logger.info(f"Found {len(jobs)} job cards on SEEK")
        return jobs

    def _fetch_with_playwright(self, url: str) -> Optional[list]:
        """Fetch SEEK jobs using Playwright with live DOM extraction."""
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
                time.sleep(4)

                page_content = page.content()
                if "captcha" in page_content.lower() or "blocked" in page_content.lower() or "just a moment" in page_content.lower():
                    self.logger.warning("SEEK blocked or CAPTCHA detected")
                    context.close()
                    browser.close()
                    return None

                jobs_data = page.evaluate("""
    () => {
        const results = [];
        const cardSelectors = [
            'article[data-job-id]',
            'div[data-job-id]',
            "div[data-automation='job-card']",
            "article[data-automation='job-card']",
            "div[data-card-type='JobCard']",
        ];
        let cards = [];
        for (const sel of cardSelectors) {
            cards = Array.from(document.querySelectorAll(sel));
            if (cards.length > 0) break;
        }

        for (const card of cards) {
            const get = (key) => {
                const el = card.querySelector('[data-automation="' + key + '"]');
                return el ? el.innerText.trim() : null;
            };

            const jobId = card.getAttribute('data-job-id') || '';
            const linkEl = card.querySelector('a[data-automation="job-list-view-job-link"], a[href*="/job/"]');
            const href = linkEl ? linkEl.getAttribute('href') : null;

            const title = get('jobTitle');
            if (!title) continue;

            results.push({
                jobId,
                title,
                company:     get('jobCompany'),
                location:    get('jobCardLocation') || get('jobLocation'),
                salary:      get('jobSalary'),
                description: get('jobShortDescription'),
                listed:      get('jobListingDate'),
                arrangement: get('work-arrangement'),
                href,
            });
        }
        return results;
    }
""")

                self.logger.info(f"Found {len(jobs_data)} job elements via Playwright")
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
        keywords_str = ",".join(keywords)
        location_encoded = quote(location)
        
        search_url = f"https://www.seek.com.au/jobs/in-Melbourne-VIC?keywords={keywords_str}"

        self.logger.info(f"SEEK search URL (HTTP fallback): {search_url}")
        
        response = self._request_with_retry(search_url, max_retries=1)
        
        if response is None:
            self.logger.warning("SEEK request failed, returning empty list")
            return jobs
        
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            
            job_cards = soup.select("article[data-job-id]")
            
            if not job_cards:
                job_cards = soup.select("div[data-test='job-card']")
            
            if not job_cards:
                job_cards = soup.select("a.job-card__wrapper")
            
            if not job_cards:
                job_cards = soup.select("div.job-card")
            
            self.logger.info(f"Found {len(job_cards)} job cards on SEEK")
            
            if len(job_cards) == 0:
                self.logger.warning("No job cards found - SEEK may be blocking or page structure changed")
                return jobs
                
            for card in job_cards:
                try:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.warning(f"Failed to parse job card: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to parse SEEK response: {e}")
            
        return jobs

    def _parse_job_card(self, card) -> Optional[RawJob]:
        """Parse a single job card from SEEK."""
        try:
            source_job_id = None
            if card.get("data-job-id"):
                source_job_id = str(card.get("data-job-id"))
            elif card.get("data-jobid"):
                source_job_id = str(card.get("data-jobid"))
            
            if not source_job_id:
                link_elem = card.select_one("a")
                if link_elem and link_elem.get("href"):
                    match = re.search(r'/job/(\d+)', link_elem.get("href", ""))
                    if match:
                        source_job_id = match.group(1)
            
            if not source_job_id:
                self.logger.debug("Could not extract job ID, skipping")
                return None
            
            title = None
            title_elem = card.select_one("h3") or card.select_one("[data-test='job-card-title']")
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if not title:
                title_elem = card.select_one("a.job-card__title")
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            if not title:
                self.logger.debug("Could not extract job title, skipping")
                return None
            
            company = None
            company_elem = card.select_one("[data-test='job-card-company-name']")
            if company_elem:
                company = company_elem.get_text(strip=True)
            
            if not company:
                company_elem = card.select_one("span.company-name")
                if company_elem:
                    company = company_elem.get_text(strip=True)
            
            if not company:
                company = "Unknown Company"
            
            location = None
            location_elem = card.select_one("[data-test='job-card-location']")
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            if not location:
                location_elem = card.select_one("span.location")
                if location_elem:
                    location = location_elem.get_text(strip=True)
            
            salary_text = None
            salary_elem = card.select_one("[data-test='job-card-salary']")
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
            
            if not salary_text:
                salary_elem = card.select_one("span.salary")
                if salary_elem:
                    salary_text = salary_elem.get_text(strip=True)
            
            description = None
            desc_elem = card.select_one("[data-test='job-card-summary']")
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            if not description:
                desc_elem = card.select_one("div.job-card__snippet")
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
            
            url = None
            link_elem = card.select_one("a")
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href", "")
                if href.startswith("http"):
                    url = href
                else:
                    url = urljoin("https://www.seek.com.au", href)
            
            if not url:
                url = f"https://www.seek.com.au/job/{source_job_id}"
            
            posted_at = None
            posted_elem = card.select_one("[data-test='job-card-listed']")
            if posted_elem:
                posted_text = posted_elem.get_text(strip=True)
                posted_at = self._parse_posted_date(posted_text)
            
            return RawJob(
                source="seek",
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
        """Parse SEEK's relative date format."""
        if not date_text:
            return None
            
        date_text = date_text.lower().strip()
        
        now = datetime.now()
        
        if "just now" in date_text or "today" in date_text:
            return now.strftime("%Y-%m-%d")
        
        if "hour" in date_text or "h ago" in date_text:
            match = re.search(r'(\d+)', date_text)
            if match:
                return now.strftime("%Y-%m-%d")
        
        if "minute" in date_text or "m ago" in date_text:
            return now.strftime("%Y-%m-%d")
        
        match = re.search(r'(\d+)d?', date_text)
        if match:
            days = int(match.group(1))
            date_obj = now - timedelta(days=days)
            return date_obj.strftime("%Y-%m-%d")
        
        match = re.search(r'(\d+)w?', date_text)
        if match:
            weeks = int(match.group(1))
            date_obj = now - timedelta(weeks=weeks)
            return date_obj.strftime("%Y-%m-%d")
        
        return None