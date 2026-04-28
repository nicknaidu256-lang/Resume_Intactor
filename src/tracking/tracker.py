"""Application tracking helpers backed by the local SQLite database."""

import logging
from pathlib import Path
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Use same DB path as database module
DB_PATH = Path("data/jobs.db")


def get_stats() -> Dict:
    """Get statistics from database."""
    if not DB_PATH.exists():
        return {"total": 0, "new": 0, "applied": 0, "interview": 0}
    
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM jobs")
        total = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
        new_count = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
        applied = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*) FROM jobs WHERE status = 'interview'")
        interview = c.fetchone()[0] or 0
        
        return {
            "total": total,
            "new": new_count,
            "applied": applied,
            "interview": interview
        }
    except Exception as e:
        logger.warning(f"Failed to get stats: {e}")
        return {"total": 0, "new": 0, "applied": 0, "interview": 0}
    finally:
        if conn:
            conn.close()


def get_recent_jobs(limit: int = 15) -> List[Dict]:
    """Get recent jobs from database."""
    if not DB_PATH.exists():
        return []
    
    conn = None
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        jobs = []
        for row in rows:
            jobs.append({
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "url": row["url"],
                "score": row["score"],
                "status": row["status"]
            })
        
        return jobs
    except Exception as e:
        logger.warning(f"Failed to get recent jobs: {e}")
        return []
    finally:
        if conn:
            conn.close()