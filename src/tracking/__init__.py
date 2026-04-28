"""Application tracking module for AU Job Application Pipeline.

Handles application status tracking, follow-up management, and dashboard views.
"""

from .tracker import (
    ApplicationTracker,
    ApplicationSummary,
    ApplicationStatus,
    create_application,
    update_status,
    add_followup,
    get_dashboard,
    get_followups,
    get_stats,
    get_recent_jobs,
)

__all__ = [
    "ApplicationTracker",
    "ApplicationSummary",
    "ApplicationStatus",
    "create_application",
    "update_status",
    "add_followup",
    "get_dashboard",
    "get_followups",
    "get_stats",
    "get_recent_jobs",
]
