"""Scraper runner - orchestrates the full job discovery pipeline."""

import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.config import config
from src.core.database import save_jobs, init_db


def run_full_scrape(
    keywords: Optional[List[str]] = None,
    location: Optional[str] = None,
) -> List[Dict]:
    """Run full scrape from SEEK and Jora.
    
    Args:
        keywords: Search keywords (default from config)
        location: Location (default from config)
        
    Returns:
        List of job dictionaries
    """
    # Use defaults from config
    if keywords is None:
        keywords = config.search_keywords if hasattr(config, 'search_keywords') else ["Process Engineer"]
        
    if location is None:
        location = config.search_location if hasattr(config, 'search_location') else "Melbourne VIC"
    
    jobs = []
    
    # Try SEEK
    try:
        from src.scrapers.seek_scraper import SeekScraper
        scraper = SeekScraper()
        results = scraper.search(keywords, location)
        for r in results:
            jobs.append({
                "source": "seek",
                "source_job_id": r.source_job_id,
                "title": r.title,
                "company": r.company,
                "location": r.location,
                "url": r.url or f"https://www.seek.com.au/job/{r.source_job_id}",
                "salary_text": r.salary_text,
                "description": r.description,
            })
        logger.info(f"SEEK: found {len(results)} jobs")
    except Exception as e:
        logger.warning(f"SEEK scrape failed: {e}")
    
    # Try Jora
    try:
        from src.scrapers.jora_scraper import JoraScraper
        scraper = JoraScraper()
        results = scraper.search(keywords, location)
        for r in results:
            jobs.append({
                "source": "jora",
                "source_job_id": r.source_job_id,
                "title": r.title,
                "company": r.company,
                "location": r.location,
                "url": r.url or f"https://au.jora.com/job/{r.source_job_id}",
                "salary_text": r.salary_text,
                "description": r.description,
            })
        logger.info(f"Jora: found {len(results)} jobs")
    except Exception as e:
        logger.warning(f"Jora scrape failed: {e}")
    
    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job.get("source", ""), job.get("source_job_id", ""))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    # Save to database
    try:
        init_db()  # Ensure DB exists
        saved = save_jobs(unique_jobs)
        logger.info(f"Saved {saved} jobs to database")
    except Exception as e:
        logger.warning(f"Failed to save jobs to DB: {e}")
    
    logger.info(f"Total unique jobs: {len(unique_jobs)}")
    return unique_jobs


def scrape_single_source(
    source: str,
    keywords: List[str],
    location: str,
) -> List[Dict]:
    """Scrape from a single source."""
    jobs = []
    
    try:
        if source == "seek":
            from src.scrapers.seek_scraper import SeekScraper
            scraper = SeekScraper()
        elif source == "jora":
            from src.scrapers.jora_scraper import JoraScraper
            scraper = JoraScraper()
        else:
            logger.warning(f"Unknown source: {source}")
            return jobs
            
        results = scraper.search(keywords, location)
        for r in results:
            jobs.append({
                "source": source,
                "source_job_id": r.source_job_id,
                "title": r.title,
                "company": r.company,
                "location": r.location,
                "url": r.url,
                "salary_text": r.salary_text,
                "description": r.description,
            })
            
    except Exception as e:
        logger.warning(f"{source} scrape failed: {e}")
    
    return jobs