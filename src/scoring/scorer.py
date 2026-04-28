"""Job scorer for AU Job Application Pipeline.

Scores jobs against a candidate profile based on multiple dimensions:
- Title match
- Skill match
- Salary fit
- Location fit
- Experience level match
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import json
import os

import logging
logger = logging.getLogger("scoring")


@dataclass
class ScoreResult:
    """Result of scoring a job."""
    job_id: int
    final_score: float
    title_score: float
    skill_score: float
    salary_score: float
    location_score: float
    experience_score: float
    score_reason: str


class JobScorer:
    """Scores jobs against candidate profile."""

    def __init__(self):
        self._use_defaults()

    def _use_defaults(self):
        """Use default weights."""
        self.title_weight = 0.25
        self.skill_weight = 0.30
        self.salary_weight = 0.20
        self.location_weight = 0.15
        self.experience_weight = 0.10

    def score_job(
        self,
        job_id: int,
        job_title: str,
        job_description: str,
        job_location: Optional[str],
        salary_min: Optional[int],
        salary_max: Optional[int],
        salary_confidence: float,
        candidate_profile: dict,
    ) -> ScoreResult:
        """Score a single job against candidate profile."""
        # Title score
        title_score = self._score_title(job_title, candidate_profile)
        
        # Skill score  
        skill_score = self._score_skills(job_title, job_description, candidate_profile)
        
        # Salary score
        salary_score = self._score_salary(salary_min, salary_max, salary_confidence, candidate_profile)
        
        # Location score
        location_score = self._score_location(job_location, candidate_profile)
        
        # Experience score
        experience_score = self._score_experience(job_title, job_description, candidate_profile)
        
        # Calculate final weighted score
        final_score = (
            title_score * self.title_weight +
            skill_score * self.skill_weight +
            salary_score * self.salary_weight +
            location_score * self.location_weight +
            experience_score * self.experience_weight
        )
        
        # Generate reason
        reason = self._generate_reason(
            title_score, skill_score, salary_score, 
            location_score, experience_score
        )
        
        return ScoreResult(
            job_id=job_id,
            final_score=round(final_score, 2),
            title_score=round(title_score, 2),
            skill_score=round(skill_score, 2),
            salary_score=round(salary_score, 2),
            location_score=round(location_score, 2),
            experience_score=round(experience_score, 2),
            score_reason=reason
        )

    def _score_title(self, title: str, profile: dict) -> float:
        """Score job title against target title."""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        target_title = profile.get("title", "").lower()
        
        # Exact match
        if target_title in title_lower or title_lower in target_title:
            return 1.0
        
        # Partial match - check key words
        target_words = set(target_title.split())
        title_words = set(title_lower.split())
        
        overlap = len(target_words & title_words)
        if overlap > 0:
            return min(overlap / len(target_words), 0.8)
        
        return 0.0

    def _score_skills(self, title: str, description: str, profile: dict) -> float:
        """Score required skills against candidate skills."""
        if not description:
            return 0.0
        
        text = f"{title} {description}".lower()
        candidate_skills = profile.get("skills", {})
        
        skill_categories = [
            skill.lower() 
            for skills in candidate_skills.values() 
            for skill in skills
        ]
        
        matches = sum(1 for skill in skill_categories if skill in text)
        
        if matches == 0:
            return 0.0
        
        # Normalize: more matches = higher score, cap at 1.0
        return min(matches / 5.0, 1.0)

    def _score_salary(
        self, 
        salary_min: Optional[int], 
        salary_max: Optional[int],
        confidence: float,
        profile: dict
    ) -> float:
        """Score salary fit."""
        if not salary_min and not salary_max:
            return 0.5  # Neutral if no salary
        
        expected = profile.get("salary", {})
        expected_min = expected.get("annual_min", 0)
        expected_max = expected.get("annual_max", 999999)
        
        # Confidence 0.1 (vague) reduces reliability
        if confidence < 0.5:
            return 0.3
        
        job_min = salary_min or salary_max or 0
        job_max = salary_max or salary_min or job_min
        
        # Check if within range
        if expected_min <= job_max and job_min <= expected_max:
            return 1.0
        
        # If below range, penalty
        if job_max < expected_min:
            return max(0.0, 1.0 - (expected_min - job_max) / expected_min)
        
        # If above range, slight penalty
        if job_min > expected_max:
            return 0.7
        
        return 0.5

    def _score_location(self, location: Optional[str], profile: dict) -> float:
        """Score location fit."""
        if not location:
            return 0.5
        
        target_location = profile.get("personal", {}).get("location", "")
        if not target_location:
            return 0.5
        
        location_lower = location.lower()
        target_lower = target_location.lower()
        
        # Exact or partial match
        if target_lower in location_lower or location_lower in target_lower:
            return 1.0
        
        # Check for common patterns (e.g., "Melbourne" in "Melbourne VIC")
        target_parts = target_lower.split()
        if any(part in location_lower for part in target_parts if len(part) > 2):
            return 0.8
        
        # Remote/hybrid might be acceptable
        if any(word in location_lower for word in ["remote", "hybrid", "work from home", "wfh"]):
            return 0.9
        
        return 0.2

    def _score_experience(
        self, 
        title: str, 
        description: str, 
        profile: dict
    ) -> float:
        """Score experience level match."""
        text = f"{title} {description}".lower()
        exp_years = profile.get("experience_years", 10)
        
        # Junior roles (require less experience)
        if any(word in text for word in ["junior", "entry", "graduate", "0-2 years", "1-2 years"]):
            return 1.0 if exp_years > 3 else 0.5
        
        # Senior roles (require more experience)
        if any(word in text for word in ["senior", "lead", "principal", "5+ years", "7+ years"]):
            return 1.0 if exp_years >= 5 else 0.4
        
        # Mid-level is usually flexible
        return 0.7

    def _generate_reason(
        self, 
        title: float, 
        skills: float, 
        salary: float,
        location: float, 
        experience: float
    ) -> str:
        """Generate human-readable reason for score."""
        parts = []
        
        if title >= 0.8:
            parts.append("Title match")
        elif title >= 0.5:
            parts.append("Partial title")
        
        if skills >= 0.8:
            parts.append("Skills aligned")
        elif skills >= 0.5:
            parts.append("Some skills match")
        
        if salary >= 0.9:
            parts.append("Salary in range")
        elif salary <= 0.3:
            parts.append("Salary below target")
        
        if location >= 0.8:
            parts.append("Good location")
        elif location <= 0.3:
            parts.append("Location mismatch")
        
        if experience >= 0.8:
            parts.append("Experience fit")
        
        return "; ".join(parts) if parts else "No strong match"


def load_candidate_profile(profile_path: str = "data/candidate_profile.json") -> dict:
    """Load candidate profile from JSON file."""
    if not os.path.exists(profile_path):
        logger.warning(f"Candidate profile not found: {profile_path}")
        return {}
    
    with open(profile_path, "r") as f:
        return json.load(f)


def score_jobs(jobs: List[dict], threshold: float = 0.45) -> List[dict]:
    """Score list of jobs and return filtered results."""
    profile = load_candidate_profile()
    
    if not profile:
        logger.error("No candidate profile loaded")
        return []
    
    scorer = JobScorer()
    results = []
    
    for job in jobs:
        result = scorer.score_job(
            job_id=job.get("id", 0),
            job_title=job.get("title", ""),
            job_description=job.get("description", ""),
            job_location=job.get("location"),
            salary_min=job.get("salary_min"),
            salary_max=job.get("salary_max"),
            salary_confidence=job.get("salary_confidence", 0.5),
            candidate_profile=profile,
        )
        
        if result.final_score >= threshold:
            results.append({
                "job_id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "url": job.get("url"),
                "score": result.final_score,
                "title_score": result.title_score,
                "skill_score": result.skill_score,
                "salary_score": result.salary_score,
                "location_score": result.location_score,
                "experience_score": result.experience_score,
                "reason": result.score_reason,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results