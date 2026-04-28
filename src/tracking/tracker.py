"""Application tracking helpers backed by the local SQLite database."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional

from src.utils import get_logger

logger = get_logger()
DB_PATH = Path(__file__).parent.parent.parent / "data" / "jobs.db"


class ApplicationStatus(Enum):
    """Application status states."""
    DISCOVERED = "discovered"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


STATUS_ORDER = {
    ApplicationStatus.DISCOVERED: 0,
    ApplicationStatus.APPLIED: 1,
    ApplicationStatus.INTERVIEW: 2,
    ApplicationStatus.OFFER: 3,
    ApplicationStatus.REJECTED: 4,
    ApplicationStatus.WITHDRAWN: 4,
}


@dataclass
class ApplicationSummary:
    """Summary of an application for dashboard display."""
    application_id: int
    job_title: str
    company: str
    status: str
    applied_at: Optional[datetime]
    next_followup: Optional[datetime]
    score: Optional[float]


class ApplicationTracker:
    """Tracks job applications and their status."""

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def create_application(
        self,
        job_id: int,
        status: str = "discovered",
        resume_path: Optional[str] = None,
        cover_letter_path: Optional[str] = None,
    ) -> dict:
        """Create a new application record.

        Args:
            job_id: Database ID of the job
            status: Initial status (default: discovered)
            resume_path: Path to resume used
            cover_letter_path: Path to cover letter used

        Returns:
            Created Application object
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'discovered',
                    applied_at TEXT,
                    resume_path TEXT,
                    cover_letter_path TEXT,
                    notes TEXT,
                    created_at TEXT
                )
                """
            )
            cur.execute(
                """
                INSERT INTO applications (job_id, status, resume_path, cover_letter_path, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, status, resume_path, cover_letter_path, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            app_id = cur.lastrowid
            logger.info(f"Created application {app_id} for job {job_id}")
            return {"id": app_id, "job_id": job_id, "status": status}
        finally:
            conn.close()

    def update_status(
        self,
        application_id: int,
        new_status: str,
        notes: Optional[str] = None,
    ) -> dict:
        """Update application status.

        Args:
            application_id: Database ID of the application
            new_status: New status value
            notes: Optional notes about the status change

        Returns:
            Updated Application object
        """
        valid_statuses = [s.value for s in ApplicationStatus]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of: {valid_statuses}")

        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT status, notes FROM applications WHERE id = ?", (application_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Application {application_id} not found")

            old_status = row["status"]
            existing_notes = row["notes"] or ""
            applied_at = datetime.now(timezone.utc).isoformat() if new_status == "applied" else None
            if notes:
                stamp = f"\n[{datetime.now(timezone.utc).isoformat()}] {notes}"
                existing_notes = existing_notes + stamp

            if applied_at:
                cur.execute(
                    "UPDATE applications SET status = ?, applied_at = COALESCE(applied_at, ?), notes = ? WHERE id = ?",
                    (new_status, applied_at, existing_notes or None, application_id),
                )
            else:
                cur.execute(
                    "UPDATE applications SET status = ?, notes = ? WHERE id = ?",
                    (new_status, existing_notes or None, application_id),
                )
            conn.commit()
            logger.info(f"Updated application {application_id} status: {old_status} -> {new_status}")
            return {"id": application_id, "status": new_status}
        finally:
            conn.close()

    def add_followup(
        self,
        application_id: int,
        followup_date: datetime,
        notes: Optional[str] = None,
    ) -> dict:
        """Add a follow-up reminder.

        Args:
            application_id: Database ID of the application
            followup_date: Date for follow-up
            notes: Optional notes about the follow-up

        Returns:
            Created Followup object
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS followups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER NOT NULL,
                    followup_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                INSERT INTO followups (application_id, followup_date, status, notes)
                VALUES (?, ?, 'pending', ?)
                """,
                (application_id, followup_date.isoformat(), notes),
            )
            conn.commit()
            followup_id = cur.lastrowid
            logger.info(f"Added followup {followup_id} for application {application_id}")
            return {"id": followup_id, "application_id": application_id}
        finally:
            conn.close()

    def get_dashboard_summary(self) -> dict:
        """Get dashboard summary with counts by status.

        Returns:
            Dictionary with status counts and application details
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            if not DB_PATH.exists():
                return {"status_counts": {}, "total": 0, "applications": []}

            table_names = {
                row[0]
                for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "jobs" not in table_names:
                return {"status_counts": {}, "total": 0, "applications": []}

            if "applications" in table_names:
                rows = cur.execute(
                    """
                    SELECT a.id AS application_id, a.status, a.applied_at,
                           j.title AS job_title, j.company AS company, j.score AS score
                    FROM applications a
                    LEFT JOIN jobs j ON j.id = a.job_id
                    ORDER BY a.id DESC
                    """
                ).fetchall()
            else:
                rows = cur.execute(
                    """
                    SELECT j.id AS application_id, 'discovered' AS status, NULL AS applied_at,
                           j.title AS job_title, j.company AS company, j.score AS score
                    FROM jobs j
                    ORDER BY j.id DESC
                    """
                ).fetchall()

            status_counts = {
                "discovered": 0,
                "applied": 0,
                "interview": 0,
                "offer": 0,
                "rejected": 0,
                "withdrawn": 0,
            }
            summaries: List[ApplicationSummary] = []
            for row in rows:
                status = row["status"] or "discovered"
                status_counts[status] = status_counts.get(status, 0) + 1
                applied_at = datetime.fromisoformat(row["applied_at"]) if row["applied_at"] else None
                summaries.append(
                    ApplicationSummary(
                        application_id=row["application_id"],
                        job_title=row["job_title"] or "Unknown",
                        company=row["company"] or "Unknown",
                        status=status,
                        applied_at=applied_at,
                        next_followup=None,
                        score=float(row["score"]) if row["score"] is not None else None,
                    )
                )

            return {"status_counts": status_counts, "total": len(summaries), "applications": summaries}
        finally:
            conn.close()

    def get_upcoming_followups(self, days: int = 7) -> List[dict]:
        """Get upcoming follow-ups within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of follow-up dictionaries
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            table_names = {
                row[0]
                for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "followups" not in table_names or "applications" not in table_names or "jobs" not in table_names:
                return []
            cutoff = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
            rows = cur.execute(
                """
                SELECT f.id AS followup_id, a.id AS application_id, j.title AS job_title,
                       j.company AS company, f.followup_date, f.notes
                FROM followups f
                JOIN applications a ON a.id = f.application_id
                LEFT JOIN jobs j ON j.id = a.job_id
                WHERE f.status = 'pending' AND f.followup_date <= ?
                ORDER BY f.followup_date
                """,
                (cutoff,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def mark_followup_complete(self, followup_id: int) -> dict:
        """Mark a follow-up as completed.

        Args:
            followup_id: Database ID of the follow-up

        Returns:
            Updated Followup object
        """
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE followups SET status = 'completed' WHERE id = ?", (followup_id,))
            conn.commit()
            logger.info(f"Marked followup {followup_id} as completed")
            return {"id": followup_id, "status": "completed"}
        finally:
            conn.close()


def create_application(
    job_id: int,
    status: str = "discovered",
    resume_path: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
) -> dict:
    """Convenience function to create an application."""
    tracker = ApplicationTracker()
    return tracker.create_application(job_id, status, resume_path, cover_letter_path)


def update_status(
    application_id: int,
    new_status: str,
    notes: Optional[str] = None,
) -> dict:
    """Convenience function to update application status."""
    tracker = ApplicationTracker()
    return tracker.update_status(application_id, new_status, notes)


def add_followup(
    application_id: int,
    followup_date: datetime,
    notes: Optional[str] = None,
) -> dict:
    """Convenience function to add a follow-up."""
    tracker = ApplicationTracker()
    return tracker.add_followup(application_id, followup_date, notes)


def get_dashboard() -> dict:
    """Convenience function to get dashboard summary."""
    tracker = ApplicationTracker()
    return tracker.get_dashboard_summary()


def get_followups(days: int = 7) -> List[dict]:
    """Convenience function to get upcoming follow-ups."""
    tracker = ApplicationTracker()
    return tracker.get_upcoming_followups(days)


def get_stats() -> dict:
    """Return lightweight dashboard stats from `data/jobs.db`."""
    summary = get_dashboard()
    status_counts = summary.get("status_counts", {})
    return {
        "total_jobs": summary.get("total", 0),
        "applied_jobs": status_counts.get("applied", 0),
        "interview_jobs": status_counts.get("interview", 0),
        "offer_jobs": status_counts.get("offer", 0),
    }


def get_recent_jobs(limit: int = 10) -> List[dict]:
    """Return recent jobs/applications for dashboard display."""
    summary = get_dashboard()
    rows = []
    for app in summary.get("applications", [])[:limit]:
        rows.append(
            {
                "application_id": app.application_id,
                "title": app.job_title,
                "company": app.company,
                "status": app.status,
                "score": app.score,
                "location": "",
            }
        )
    return rows
