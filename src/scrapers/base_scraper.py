"""Base scraper module for AU Job Application Pipeline.

Provides shared infrastructure for all job source scrapers:
- Rate limiting with configurable delays
- Retry logic for transient failures
- Error isolation (one source failure doesn't crash pipeline)
- HTTP session management with AU user-agent
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

import httpx

from src.utils import get_logger


@dataclass
class RawJob:
    """Raw job data from a scraper before normalisation."""
    source: str
    source_job_id: str
    title: str
    company: str
    url: str
    location: Optional[str] = None
    salary_text: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[str] = None


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    def __init__(self, name: str, min_delay_seconds: int = 2):
        """Initialise the scraper.
        
        Args:
            name: Scraper name (e.g., 'seek', 'jora')
            min_delay_seconds: Minimum delay between requests
        """
        self.name = name
        self.min_delay_seconds = min_delay_seconds
        self.logger = get_logger(f"scraper.{name}")
        self._last_request_time: Optional[float] = None
        self._session: Optional[httpx.Client] = None

    @property
    def delay_seconds(self) -> int:
        """Get configured delay, respecting minimum for this source."""
        # Use a default of 2 seconds if no config available
        return max(2, self.min_delay_seconds)

    def _get_session(self) -> httpx.Client:
        """Get or create HTTP session with AU headers."""
        if self._session is None:
            self._session = httpx.Client(
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-AU,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                follow_redirects=True,
            )
        return self._session

    def _wait_before_request(self):
        """Apply rate limiting delay before making a request."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay_seconds:
                sleep_time = self.delay_seconds - elapsed
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _request_with_retry(self, url: str, max_retries: int = 1) -> Optional[httpx.Response]:
        """Make HTTP request with retry logic.

        Args:
            url: URL to fetch
            max_retries: Number of retries on failure (default 1)

        Returns:
            Response object or None on failure
        """
        self._wait_before_request()

        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"Fetching: {url} (attempt {attempt + 1})")
                response = self._get_session().get(url)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                self.logger.warning(f"HTTP error {e.response.status_code} for {url}")
                if attempt < max_retries:
                    self.logger.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    self.logger.error(f"Failed after {max_retries + 1} attempts: {url}")
                    return None
            except httpx.RequestError as e:
                self.logger.warning(f"Request error: {e}")
                if attempt < max_retries:
                    self.logger.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    self.logger.error(f"Failed after {max_retries + 1} attempts: {url}")
                    return None

        return None

    def close(self):
        """Close the HTTP session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    @abstractmethod
    def search(self, keywords: List[str], location: str) -> List[RawJob]:
        """Search for jobs.
        
        Args:
            keywords: List of search keywords
            location: Location to search in
            
        Returns:
            List of raw job data dictionaries
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class ScraperError(Exception):
    """Exception raised when a scraper encounters a non-recoverable error."""
    pass


def run_scraper_safe(scraper: BaseScraper, keywords: List[str], location: str) -> List[RawJob]:
    """Run a scraper with error isolation.
    
    If the scraper fails, returns empty list and logs error but doesn't crash.
    
    Args:
        scraper: Scraper instance to run
        keywords: Search keywords
        location: Search location
        
    Returns:
        List of raw jobs (empty on failure)
    """
    logger = get_logger(f"scraper.safe.{scraper.name}")
    try:
        logger.info(f"Starting scrape: {scraper.name}")
        results = scraper.search(keywords, location)
        logger.info(f"Scraped {len(results)} jobs from {scraper.name}")
        return results
    except Exception as e:
        logger.error(f"Scraper {scraper.name} failed: {e}")
        logger.info(f"Pipeline continuing - returning empty list for {scraper.name}")
        return []
    finally:
        scraper.close()