"""Simple SQLite database for job tracking."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict

DB_PATH = Path("data/jobs.db")


def get_connection():
    """Get database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            source_job_id TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            salary_text TEXT,
            description TEXT,
            score REAL DEFAULT 0.0,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_job(job: Dict) -> int:
    """Save a job to database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO jobs (source, source_job_id, title, company, location, url, salary_text, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("source"),
        job.get("source_job_id"),
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("url"),
        job.get("salary_text"),
        job.get("description"),
        "new"
    ))
    conn.commit()
    job_id = c.lastrowid
    conn.close()
    return job_id


def save_jobs(jobs: List[Dict]) -> int:
    """Save multiple jobs to database."""
    conn = get_connection()
    c = conn.cursor()
    count = 0
    for job in jobs:
        c.execute("""
            INSERT INTO jobs (source, source_job_id, title, company, location, url, salary_text, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("source"),
            job.get("source_job_id"),
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("url"),
            job.get("salary_text"),
            job.get("description"),
            "new"
        ))
        count += 1
    conn.commit()
    conn.close()
    return count


def get_jobs(limit: int = 50, status: Optional[str] = None) -> List[Dict]:
    """Get jobs from database."""
    conn = get_connection()
    c = conn.cursor()
    
    if status:
        c.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
    else:
        c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    
    columns = [description[0] for description in c.description]
    jobs = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return jobs


def get_stats() -> Dict:
    """Get statistics from database."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM jobs")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
    new_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
    applied = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'interview'")
    interview = c.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total,
        "new": new_count,
        "applied": applied,
        "interview": interview
    }


# Initialize on import
init_db()