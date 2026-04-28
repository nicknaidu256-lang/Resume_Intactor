"""Application tracking module for AU Job Application Pipeline.

Handles application status tracking, follow-up management, and dashboard views.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, List

from src.core.database import get_session, Job, Application, Followup
from src.utils import get_logger

logger = get_logger("tracking")


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
        pass

    def create_application(
        self,
        job_id: int,
        status: str = "discovered",
        resume_path: Optional[str] = None,
        cover_letter_path: Optional[str] = None,
    ) -> Application:
        """Create a new application record.

        Args:
            job_id: Database ID of the job
            status: Initial status (default: discovered)
            resume_path: Path to resume used
            cover_letter_path: Path to cover letter used

        Returns:
            Created Application object
        """
        session = get_session()

        try:
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            application = Application(
                job_id=job_id,
                status=status,
                resume_path=resume_path,
                cover_letter_path=cover_letter_path,
                created_at=datetime.now(timezone.utc),
            )

            session.add(application)
            session.commit()
            session.refresh(application)

            logger.info(f"Created application {application.id} for job {job_id}")

            return application

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create application: {e}")
            raise
        finally:
            session.close()

    def update_status(
        self,
        application_id: int,
        new_status: str,
        notes: Optional[str] = None,
    ) -> Application:
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

        session = get_session()

        try:
            application = session.query(Application).filter(
                Application.id == application_id
            ).first()

            if not application:
                raise ValueError(f"Application {application_id} not found")

            old_status = application.status
            application.status = new_status

            if new_status == "applied" and not application.applied_at:
                application.applied_at = datetime.now(timezone.utc)

            if notes:
                application.notes = (application.notes or "") + f"
[{datetime.now(timezone.utc).isoformat()}] {notes}"

            session.commit()
            session.refresh(application)

            logger.info(f"Updated application {application_id} status: {old_status} -> {new_status}")

            return application

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update status: {e}")
            raise
        finally:
            session.close()

    def add_followup(
        self,
        application_id: int,
        followup_date: datetime,
        notes: Optional[str] = None,
    ) -> Followup:
        """Add a follow-up reminder.

        Args:
            application_id: Database ID of the application
            followup_date: Date for follow-up
            notes: Optional notes about the follow-up

        Returns:
            Created Followup object
        """
        session = get_session()

        try:
            application = session.query(Application).filter(
                Application.id == application_id
            ).first()

            if not application:
                raise ValueError(f"Application {application_id} not found")

            followup = Followup(
                application_id=application_id,
                followup_date=followup_date,
                status="pending",
                notes=notes,
            )

            session.add(followup)
            session.commit()
            session.refresh(followup)

            logger.info(f"Added followup {followup.id} for application {application_id}")     

            return followup

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add followup: {e}")
            raise
        finally:
            session.close()

    def get_dashboard_summary(self) -> dict:
        """Get dashboard summary with counts by status.

        Returns:
            Dictionary with status counts and application details
        """
        session = get_session()

        try:
            now = datetime.now(timezone.utc)

            applications_with_job = (
                session.query(Application, Job)
                .join(Job, Application.job_id == Job.id)
                .all()
            )

            pending_followups = (
                session.query(Followup)
                .filter(
                    Followup.followup_date >= now,
                    Followup.status == "pending"
                )
                .order_by(Followup.application_id, Followup.followup_date)
                .all()
            )

            followup_by_app_id = {}
            for fu in pending_followups:
                if fu.application_id not in followup_by_app_id:
                    followup_by_app_id[fu.application_id] = fu.followup_date

            status_counts = {
                "discovered": 0,
                "applied": 0,
                "interview": 0,
                "offer": 0,
                "rejected": 0,
                "withdrawn": 0,
            }

            summaries = []

            for app, job in applications_with_job:
                status_counts[app.status] = status_counts.get(app.status, 0) + 1

                next_followup = followup_by_app_id.get(app.id)

                summaries.append(ApplicationSummary(
                    application_id=app.id,
                    job_title=job.title if job else "Unknown",
                    company=job.company if job else "Unknown",
                    status=app.status,
                    applied_at=app.applied_at,
                    next_followup=next_followup,
                    score=job.score if job else None,
                ))

            summaries.sort(key=lambda s: STATUS_ORDER.get(
                ApplicationStatus(s.status), 99
            ))

            return {
                "status_counts": status_counts,
                "total": len(applications_with_job),
                "applications": summaries,
            }

        finally:
            session.close()

    def get_upcoming_followups(self, days: int = 7) -> List[dict]:
        """Get upcoming follow-ups within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of follow-up dictionaries
        """
        session = get_session()

        try:
            cutoff = datetime.now(timezone.utc) + timedelta(days=days)

            followups = session.query(Followup).filter(
                Followup.followup_date <= cutoff,
                Followup.status == "pending"
            ).order_by(Followup.followup_date).all()

            results = []

            for followup in followups:
                app = session.query(Application).filter(
                    Application.id == followup.application_id
                ).first()

                if app:
                    job = session.query(Job).filter(Job.id == app.job_id).first()

                    results.append({
                        "followup_id": followup.id,
                        "application_id": app.id,
                        "job_title": job.title if job else "Unknown",
                        "company": job.company if job else "Unknown",
                        "followup_date": followup.followup_date,
                        "notes": followup.notes,
                    })

            return results

        finally:
            session.close()

    def mark_followup_complete(self, followup_id: int) -> Followup:
        """Mark a follow-up as completed.

        Args:
            followup_id: Database ID of the follow-up

        Returns:
            Updated Followup object
        """
        session = get_session()

        try:
            followup = session.query(Followup).filter(
                Followup.id == followup_id
            ).first()

            if not followup:
                raise ValueError(f"Followup {followup_id} not found")

            followup.status = "completed"
            session.commit()
            session.refresh(followup)

            logger.info(f"Marked followup {followup.id} as completed")

            return followup

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to mark followup complete: {e}")
            raise
        finally:
            session.close()


def create_application(
    job_id: int,
    status: str = "discovered",
    resume_path: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
) -> Application:
    """Convenience function to create an application."""
    tracker = ApplicationTracker()
    return tracker.create_application(job_id, status, resume_path, cover_letter_path)


def update_status(
    application_id: int,
    new_status: str,
    notes: Optional[str] = None,
) -> Application:
    """Convenience function to update application status."""
    tracker = ApplicationTracker()
    return tracker.update_status(application_id, new_status, notes)


def add_followup(
    application_id: int,
    followup_date: datetime,
    notes: Optional[str] = None,
) -> Followup:
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
