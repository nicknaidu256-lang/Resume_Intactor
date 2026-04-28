"""
Job Description Parser.
Extracts structured information from raw job posting text.
Uses regex and heuristics; no heavy NLP dependencies.
"""

import re
import logging
from typing import Dict, List, Tuple
from src.utils import get_logger

logger = get_logger()


class JobParser:
    """Parse job descriptions into structured data."""

    def __init__(self):
        """Initialize parser with regex patterns."""
        # Skills: look for common section headers
        self.skills_patterns = [
            r"required skills[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"qualifications[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"requirements[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
        ]

        # Bullet points (lines starting with • or - or *)
        self.bullet_regex = r"^[\s]*[•\-\*][\s]+(.+)$"

    def parse(self, text: str) -> dict:
        """
        Parse job description text.

        Args:
            text: Raw job description

        Returns:
            Dict with keys: title, company, required_skills, preferred_skills,
            keywords, responsibilities, raw_text
        """
        logger.info("Parsing job description")

        lines = text.strip().split("\n")
        result = {
            "title": self._extract_title(lines),
            "company": self._extract_company(lines),
            "required_skills": [],
            "preferred_skills": [],
            "keywords": [],
            "responsibilities": [],
            "raw_text": text
        }

        # Extract required skills
        required_text = self._extract_section(text, [
            r"required skills[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"requirements[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"qualifications[:\s]*\n([\s\S]*?)(?=\n\n|\Z)"
        ])
        if required_text:
            result["required_skills"] = self._extract_bullet_items(required_text)
            logger.debug(f"Extracted required skills: {result['required_skills']}")

        # Extract preferred skills separately
        preferred_text = self._extract_section(text, [
            r"preferred skills[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"preferred[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"nice to have[:\s]*\n([\s\S]*?)(?=\n\n|\Z)",
            r"optional[:\s]*\n([\s\S]*?)(?=\n\n|\Z)"
        ])
        if preferred_text:
            result["preferred_skills"] = self._extract_bullet_items(preferred_text)
            logger.debug(f"Extracted preferred skills: {result['preferred_skills']}")

        # Extract responsibilities (bullet points)
        result["responsibilities"] = self._extract_responsibilities(text)

        # Extract keywords (n-grams from title and skills)
        result["keywords"] = self._extract_keywords(text, result)

        logger.info(f"Parsed: {len(result['required_skills'])} required skills, "
                    f"{len(result['preferred_skills'])} preferred, "
                    f"{len(result['responsibilities'])} responsibilities")

        return result

    def _extract_title(self, lines: List[str]) -> str:
        """Extract job title (usually first non-empty line)."""
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                return line
        return "Unknown Position"

    def _extract_company(self, lines: List[str]) -> str:
        """
        Extract company name.
        Heuristics: look for patterns like "at Company", "Company:", "@Company", etc.
        """
        # Look for a line starting with "at " (common in JDs)
        for line in lines[:5]:
            stripped = line.strip()
            if stripped.lower().startswith("at "):
                return stripped[3:].strip()
            if stripped.startswith("@"):
                return stripped[1:].strip()

        # Fallback: try regex on joined text
        text = " ".join(lines[:10])

        # Pattern: "Company: <name>"
        match = re.search(r"[Cc]ompany\s*[:\-]\s*([^\n]+)", text)
        if match:
            return match.group(1).strip()

        # Pattern: "at <Company>" at end of string or followed by punctuation
        match = re.search(r"at\s+([A-Za-z0-9\s]+?)(?:\s*$|[,\.)]|\n)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Unknown Company"

    def _extract_section(self, text: str, patterns: List[str]) -> str:
        """Extract a section by regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _split_required_preferred(self, text: str) -> Tuple[str, str]:
        """
        Split skills into required and preferred.
        Looks for section dividers like "Required:", "Preferred:", "Nice to have".
        """
        required = []
        preferred = []

        lines = text.split("\n")
        current_section = "required"

        for line in lines:
            line_lower = line.lower().strip()
            if "preferred" in line_lower or "nice to have" in line_lower or "optional" in line_lower:
                current_section = "preferred"
                continue
            if "required" in line_lower or "must have" in line_lower or "essential" in line_lower:
                current_section = "required"
                continue

            item = line.strip()
            if item:
                if current_section == "required":
                    required.append(item)
                else:
                    preferred.append(item)

        return "\n".join(required), "\n".join(preferred)

    def _extract_bullet_items(self, text: str) -> List[str]:
        """Extract bullet items from multi-line text."""
        items = []
        for line in text.split("\n"):
            line = line.strip()
            # Remove leading bullet chars and whitespace
            line = re.sub(r"^[\s]*[•\-\*]\s*", "", line)
            if line:
                items.append(line)
        return items

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibility bullet points."""
        items = []
        for line in text.split("\n"):
            match = re.match(self.bullet_regex, line)
            if match:
                items.append(match.group(1).strip())
        return items

    def _extract_keywords(self, text: str, parsed: dict) -> List[str]:
        """
        Extract important keywords from title, skills, and responsibilities.
        Simple n-gram extraction; deduplicate and filter.
        """
        keywords = set()

        # From title (individual words, excluding stop words)
        stop_words = {"the", "and", "or", "for", "with", "in", "at", "a", "an", "of", "to", "is", "are"}
        title_words = parsed["title"].lower().split()
        for word in title_words:
            word = word.strip(".,!?()[]{}")
            if word and word not in stop_words and len(word) > 2:
                keywords.add(word)

        # From skills
        for skill_list in [parsed["required_skills"], parsed["preferred_skills"]]:
            for skill in skill_list:
                # Split on common separators
                for part in re.split(r"[,;/]\s*", skill):
                    part = part.strip().lower()
                    if part and part not in stop_words and len(part) > 2:
                        keywords.add(part)

        # From responsibilities
        for resp in parsed["responsibilities"]:
            for word in resp.lower().split():
                word = word.strip(".,!?()[]{}")
                if word and word not in stop_words and len(word) > 2:
                    keywords.add(word)

        keyword_list = sorted(list(keywords))
        logger.debug(f"Extracted {len(keyword_list)} keywords")
        return keyword_list


def parse_job_description(text: str) -> dict:
    """
    Convenience function to parse job description.

    Args:
        text: Job description text

    Returns:
        Parsed job data dictionary
    """
    parser = JobParser()
    return parser.parse(text)
