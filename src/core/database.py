"""Database module for AU Job Application Pipeline."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker 

from .config import get_settings
from .logger import get_logger


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Job(Base):
    """Job listing model."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_job_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    salary_text: Mapped[Optional[str]] = mapped_column(String(255))
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    salary_confidence: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    description: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    score: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))
    score_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="job")
    documents: Mapped[list["Document"]] = relationship(back_populates="job")


class Application(Base):
    """Job application model."""
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)       
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="discovered")     
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    portal_type: Mapped[Optional[str]] = mapped_column(String(50))
    resume_path: Mapped[Optional[str]] = mapped_column(String(500))
    cover_letter_path: Mapped[Optional[str]] = mapped_column(String(500))
    submission_result: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    next_follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["Job"] = relationship(back_populates="applications")
    followups: Mapped[list["Followup"]] = relationship(back_populates="application")
    portal_attempts: Mapped[list["PortalAttempt"]] = relationship(back_populates="application")


class Document(Base):
    """Generated document model (resume/cover letter)."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)       
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["Job"] = relationship(back_populates="documents")


class Followup(Base):
    """Follow-up reminder model."""
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    followup_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")        
    notes: Mapped[Optional[str]] = mapped_column(Text)

    application: Mapped["Application"] = relationship(back_populates="followups")


class PortalAttempt(Base):
    """Portal automation attempt log."""
    __tablename__ = "portal_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    portal_name: Mapped[str] = mapped_column(String(50), nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="portal_attempts")       


_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_path = settings.database.database_path

        db_file = Path(__file__).parent.parent.parent / db_path
        db_file.parent.mkdir(parents=True, exist_ok=True)

        database_url = f"sqlite:///{db_file}"
        _engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session():
    """Get a new database session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)    
    return _SessionLocal()


def init_db():
    """Initialize database tables."""
    logger = get_logger(__name__)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
