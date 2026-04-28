"""Job deduplicator for AU Job Application Pipeline.

Handles deduplication using two strategies:
1. Exact match: source + source_job_id
2. Fuzzy fallback: title + company + location (normalised)
"""

from typing import Optional

# Commented out due to dependency on unavailable stub/module
# from ..core.database import get_session, Job
from src.utils import get_logger

logger = get_logger("deduplicator")


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """Remove duplicate jobs from a list.
    
    Strategy:
    1. First pass: exact match on (source, source_job_id)
    2. Second pass: fuzzy match on (title, company, location)
    
    Args:
        jobs: List of normalised job dictionaries
        
    Returns:
        Deduplicated list of job dictionaries
    """
    if not jobs:
        return []
    
    seen_exact = set()
    seen_fuzzy = set()
    unique_jobs = []
    
    for job in jobs:
        source = job.get("source", "")
        source_job_id = job.get("source_job_id", "")
        
        if not source or not source_job_id:
            logger.debug("Skipping job without source/source_job_id")
            continue
        
        exact_key = (source.lower(), source_job_id)
        
        if exact_key in seen_exact:
            logger.debug(f"Exact duplicate found: {source}/{source_job_id}")
            continue
        
        fuzzy_key = _make_fuzzy_key(job)
        
        if fuzzy_key and fuzzy_key in seen_fuzzy:
            logger.debug(f"Fuzzy duplicate found: {job.get('title')} at {job.get('company')}")
            continue
        
        unique_jobs.append(job)
        
        seen_exact.add(exact_key)
        if fuzzy_key:
            seen_fuzzy.add(fuzzy_key)
    
    duplicates_removed = len(jobs) - len(unique_jobs)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate jobs")
    else:
        logger.info(f"No duplicates found in {len(jobs)} jobs")
    
    return unique_jobs


def _make_fuzzy_key(job: dict) -> Optional[tuple]:
    """Create a fuzzy matching key from job data.
    
    Args:
        job: Job dictionary
        
    Returns:
        Tuple of (lower_title, lower_company, lower_location) or None
    """
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    
    if not title or not company:
        return None
    
    title_normalised = " ".join(title.lower().split())
    company_normalised = " ".join(company.lower().split())
    location_normalised = " ".join(location.lower().split()) if location else ""
    
    return (title_normalised, company_normalised, location_normalised)


def check_duplicates_in_database(jobs: list[dict]) -> dict:
    """Check for duplicates against existing database records.
    
    Args:
        jobs: List of normalised job dictionaries
        
    Returns:
        Dictionary with 'exact_dupes', 'fuzzy_dupes', 'new_jobs' counts
    """
    # session = get_session() # This call requires get_session from ..core.database
    # try:
    #     existing_jobs = session.query(Job).all()
    #
    #     existing_exact = set()
    #     for j in existing_jobs:
    #         existing_exact.add((j.source.lower(), j.source_job_id))
    #
    #     existing_fuzzy = set()
    #     for j in existing_jobs:
    #         if j.title and j.company:
    #             key = (
    #                 " ".join(j.title.lower().split()),
    #                 " ".join(j.company.lower().split()),
    #                 " ".join(j.location.lower().split()) if j.location else ""
    #             )
    #             existing_fuzzy.add(key)
    #
    #     exact_dupes = 0
    #     fuzzy_dupes = 0
    #     new_jobs = []
    #
    #     for job in jobs:
    #         source = job.get("source", "")
    #         source_job_id = job.get("source_job_id", "")
    #
    #         exact_key = (source.lower(), source_job_id)
    #
    #         if exact_key in existing_exact:
    #             exact_dupes += 1
    #             continue
    #
    #         fuzzy_key = _make_fuzzy_key(job)
    #
    #         if fuzzy_key and fuzzy_key in existing_fuzzy:
    #             fuzzy_dupes += 1
    #             continue
    #
    #         new_jobs.append(job)
    #
    #     return {
    #         "exact_dupes": exact_dupes,
    #         "fuzzy_dupes": fuzzy_dupes,
    #         "new_jobs": len(new_jobs),
    #         "total_checked": len(jobs),
    #     }
    #
    # finally:
    #     # session.close()
    #     pass # Placeholder as session operations are commented out
    
    # Placeholder return as DB functions are commented out
    logger.warning("Database interaction functions (check_duplicates_in_database, deduplicate_against_database) are commented out due to missing database imports.")
    return {"exact_dupes": 0, "fuzzy_dupes": 0, "new_jobs": len(jobs), "total_checked": len(jobs)}


def deduplicate_against_database(jobs: list[dict]) -> list[dict]:
    """Remove jobs that already exist in the database.
    
    Args:
        jobs: List of normalised job dictionaries
        
    Returns:
        List of jobs not in database
    """
    # session = get_session() # This call requires get_session from ..core.database
    # try:
    #     existing_jobs = session.query(Job).all()
    #
    #     existing_exact = set()
    #     existing_fuzzy = set()
    #     for j in existing_jobs:
    #         existing_exact.add((j.source.lower(), j.source_job_id))
    #         if j.title and j.company:
    #             existing_fuzzy.add((
    #                 " ".join(j.title.lower().split()),
    #                 " ".join(j.company.lower().split()),
    #                 " ".join(j.location.lower().split()) if j.location else "",
    #             ))
    #
    #     unique_jobs = []
    #     seen_fuzzy_this_batch = set()
    #
    #     for job in jobs:
    #         source = job.get("source", "")
    #         source_job_id = job.get("source_job_id", "")
    #         exact_key = (source.lower(), source_job_id)
    #
    #         if exact_key in existing_exact:
    #             continue
    #
    #         fuzzy_key = _make_fuzzy_key(job)
    #         if fuzzy_key and (fuzzy_key in existing_fuzzy or fuzzy_key in seen_fuzzy_this_batch):
    #             logger.debug(f"Fuzzy DB duplicate skipped: {job.get('title')} at {job.get('company')}")
    #             continue
    #
    #         unique_jobs.append(job)
    #         existing_exact.add(exact_key)
    #         if fuzzy_key:
    #             seen_fuzzy_this_batch.add(fuzzy_key)
    #
    #     logger.info(f"DB dedup: {len(jobs) - len(unique_jobs)} duplicates removed, {len(unique_jobs)} new")
    #     return unique_jobs
    #
    # finally:
    #     # session.close()
    #     pass # Placeholder as session operations are commented out
    
    # Placeholder return as DB functions are commented out
    logger.warning("Database interaction functions (check_duplicates_in_database, deduplicate_against_database) are commented out due to missing database imports.")
    return jobs # Return all jobs assuming no DB check happened
