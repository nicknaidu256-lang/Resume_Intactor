"""Salary parser for AU Job Application Pipeline.

Regex-based extraction of salary values from raw text.
"""

import re
from dataclasses import dataclass
from typing import Optional

from src.utils import get_logger

logger = get_logger("salary.parser")


@dataclass
class ParsedSalary:
    """Parsed salary result with confidence."""
    salary_min: Optional[int]
    salary_max: Optional[int]
    confidence: float
    period: Optional[str] = None


class SalaryParser:
    """Regex-based salary parser for Australian job listings."""

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for salary extraction."""
        
        # Exact range patterns (confidence 1.0)
        self._exact_range_patterns = [
            re.compile(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[-–]\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})*)\s*-\s*\$(\d+(?:,\d{3})*)', re.IGNORECASE),
        ]
        
        # K shorthand patterns (confidence 1.0)
        self._k_shorthand_pattern = re.compile(r'\$(\d+)k\s*[-–]\s*\$(\d+)k', re.IGNORECASE)
        
        # Single bound patterns (confidence 0.9)
        self._upper_bound_patterns = [
            re.compile(r'up to\s*\$(\d{1,3}(?:,\d{3})*)', re.IGNORECASE),
            re.compile(r'maximum\s*\$(\d{1,3}(?:,\d{3})*)', re.IGNORECASE),
            re.compile(r'to\s*\$(\d{1,3}(?:,\d{3})*)', re.IGNORECASE),
        ]
        
        self._lower_bound_patterns = [
            re.compile(r'from\s*\$(\d{1,3}(?:,\d{3})*)', re.IGNORECASE),
            re.compile(r'starting\s*(?:at)?\s*\$(\d{1,3}(?:,\d{3})*)', re.IGNORECASE),
            re.compile(r'from\s*(\d+)k', re.IGNORECASE),
        ]
        
        # Hourly rate patterns (confidence 0.8)
        self._hourly_patterns = [
            re.compile(r'\$(\d+(?:\.\d+)?)\s*(?:per\s*)?hour', re.IGNORECASE),
            re.compile(r'\$(\d+(?:\.\d+)?)\s*hr', re.IGNORECASE),
            re.compile(r'\$(\d+(?:\.\d+)?)\s*/\s*hr', re.IGNORECASE),
        ]
        
        # Daily rate patterns (confidence 0.8)
        self._daily_patterns = [
            re.compile(r'\$(\d+(?:,\d{3})?)\s*(?:per\s*)?day', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})?)\s*per\s*diem', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})?)\s*/\s*day', re.IGNORECASE),
        ]
        
        # Weekly rate patterns (confidence 0.8)
        self._weekly_patterns = [
            re.compile(r'\$(\d+(?:,\d{3})?)\s*(?:per\s*)?week', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})?)\s*pw', re.IGNORECASE),
        ]
        
        # Fortnightly patterns (confidence 0.8)
        self._fortnightly_patterns = [
            re.compile(r'\$(\d+(?:,\d{3})?)\s*(?:per\s*)?fortnight', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})?)\s*pf', re.IGNORECASE),
        ]
        
        # Monthly patterns (confidence 0.8)
        self._monthly_patterns = [
            re.compile(r'\$(\d+(?:,\d{3})?)\s*(?:per\s*)?month', re.IGNORECASE),
            re.compile(r'\$(\d+(?:,\d{3})?)\s*pm', re.IGNORECASE),
        ]
        
        # Vague text patterns (confidence 0.1)
        self._vague_patterns = [
            re.compile(r'competitive', re.IGNORECASE),
            re.compile(r'attractive', re.IGNORECASE),
            re.compile(r'salary on application', re.IGNORECASE),
            re.compile(r'negotiable', re.IGNORECASE),
            re.compile(r'discuss', re.IGNORECASE),
            re.compile(r'remuneration', re.IGNORECASE),
        ]

    def parse(self, salary_text: Optional[str]) -> ParsedSalary:
        """Parse salary text and return parsed values with confidence.
        
        Args:
            salary_text: Raw salary text from job listing
            
        Returns:
            ParsedSalary with min, max, and confidence
        """
        if not salary_text or not salary_text.strip():
            return ParsedSalary(salary_min=None, salary_max=None, confidence=0.0)
        
        salary_text = salary_text.strip()
        
        # Try exact range first
        result = self._try_exact_range(salary_text)
        if result:
            return result
        
        # Try K shorthand
        result = self._try_k_shorthand(salary_text)
        if result:
            return result
        
        # Try single bounds
        result = self._try_upper_bound(salary_text)
        if result:
            return result
        
        result = self._try_lower_bound(salary_text)
        if result:
            return result
        
        # Try hourly
        result = self._try_hourly(salary_text)
        if result:
            return result
        
        # Try daily
        result = self._try_daily(salary_text)
        if result:
            return result
        
        # Try weekly
        result = self._try_weekly(salary_text)
        if result:
            return result
        
        # Try fortnightly
        result = self._try_fortnightly(salary_text)
        if result:
            return result
        
        # Try monthly
        result = self._try_monthly(salary_text)
        if result:
            return result
        
        # Check for vague text
        if self._is_vague(salary_text):
            return ParsedSalary(salary_min=None, salary_max=None, confidence=0.1)
        
        # No match found - unknown
        logger.debug(f"No salary pattern matched for: {salary_text}")
        return ParsedSalary(salary_min=None, salary_max=None, confidence=0.0)

    def _parse_number(self, text: str) -> Optional[int]:
        """Parse number string and return integer."""
        if not text:
            return None
        text = text.replace(",", "").replace(" ", "")
        try:
            return int(float(text))
        except (ValueError, TypeError):
            return None

    def _try_exact_range(self, text: str) -> Optional[ParsedSalary]:
        """Try to match exact range pattern."""
        for pattern in self._exact_range_patterns:
            match = pattern.search(text)
            if match:
                min_val = self._parse_number(match.group(1))
                max_val = self._parse_number(match.group(2))
                if min_val and max_val:
                    return ParsedSalary(salary_min=min_val, salary_max=max_val, confidence=1.0)
        return None

    def _try_k_shorthand(self, text: str) -> Optional[ParsedSalary]:
        """Try to match K shorthand pattern."""
        match = self._k_shorthand_pattern.search(text)
        if match:
            min_val = int(match.group(1)) * 1000
            max_val = int(match.group(2)) * 1000
            return ParsedSalary(salary_min=min_val, salary_max=max_val, confidence=1.0)
        return None

    def _try_upper_bound(self, text: str) -> Optional[ParsedSalary]:
        """Try to match upper bound pattern."""
        for pattern in self._upper_bound_patterns:
            match = pattern.search(text)
            if match:
                max_val = self._parse_number(match.group(1))
                if max_val:
                    return ParsedSalary(salary_min=None, salary_max=max_val, confidence=0.9)
        return None

    def _try_lower_bound(self, text: str) -> Optional[ParsedSalary]:
        """Try to match lower bound pattern."""
        # Check for k shorthand in lower bound
        match = re.search(r'from\s*(\d+)k', text, re.IGNORECASE)
        if match:
            min_val = int(match.group(1)) * 1000
            return ParsedSalary(salary_min=min_val, salary_max=None, confidence=0.9)
        
        for pattern in self._lower_bound_patterns:
            match = pattern.search(text)
            if match:
                min_val = self._parse_number(match.group(1))
                if min_val:
                    return ParsedSalary(salary_min=min_val, salary_max=None, confidence=0.9)
        return None

    def _try_hourly(self, text: str) -> Optional[ParsedSalary]:
        """Try to match hourly rate pattern."""
        for pattern in self._hourly_patterns:
            match = pattern.search(text)
            if match:
                rate = self._parse_number(match.group(1))
                if rate:
                    return ParsedSalary(salary_min=rate, salary_max=rate, confidence=0.8, period="hourly")
        return None

    def _try_daily(self, text: str) -> Optional[ParsedSalary]:
        """Try to match daily rate pattern."""
        for pattern in self._daily_patterns:
            match = pattern.search(text)
            if match:
                rate = self._parse_number(match.group(1))
                if rate:
                    return ParsedSalary(salary_min=rate, salary_max=rate, confidence=0.8, period="daily")
        return None

    def _try_weekly(self, text: str) -> Optional[ParsedSalary]:
        """Try to match weekly rate pattern."""
        for pattern in self._weekly_patterns:
            match = pattern.search(text)
            if match:
                rate = self._parse_number(match.group(1))
                if rate:
                    return ParsedSalary(salary_min=rate, salary_max=rate, confidence=0.8, period="weekly")
        return None

    def _try_fortnightly(self, text: str) -> Optional[ParsedSalary]:
        """Try to match fortnightly rate pattern."""
        for pattern in self._fortnightly_patterns:
            match = pattern.search(text)
            if match:
                rate = self._parse_number(match.group(1))
                if rate:
                    return ParsedSalary(salary_min=rate, salary_max=rate, confidence=0.8, period="fortnightly")
        return None

    def _try_monthly(self, text: str) -> Optional[ParsedSalary]:
        """Try to match monthly rate pattern."""
        for pattern in self._monthly_patterns:
            match = pattern.search(text)
            if match:
                rate = self._parse_number(match.group(1))
                if rate:
                    return ParsedSalary(salary_min=rate, salary_max=rate, confidence=0.8, period="monthly")
        return None

    def _is_vague(self, text: str) -> bool:
        """Check if text contains vague salary indicators."""
        text_lower = text.lower()
        for pattern in self._vague_patterns:
            if pattern.search(text_lower):
                return True
        return False


def parse_salary(salary_text: Optional[str]) -> ParsedSalary:
    """Convenience function to parse salary text.
    
    Args:
        salary_text: Raw salary text from job listing
        
    Returns:
        ParsedSalary with min, max, and confidence
    """
    parser = SalaryParser()
    return parser.parse(salary_text)