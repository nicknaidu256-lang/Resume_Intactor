"""Salary normaliser for AU Job Application Pipeline.

Handles annualisation and AUD conversion of salary values.
"""

from dataclasses import dataclass
from typing import Optional

from src.utils import get_logger

logger = get_logger("salary.normaliser")


# Annualisation constants (Australian standard)
HOURLY_TO_ANNUAL = 2000
DAILY_TO_ANNUAL = 250
WEEKLY_TO_ANNUAL = 52
FORTNIGHTLY_TO_ANNUAL = 26
MONTHLY_TO_ANNUAL = 12


@dataclass
class NormalisedSalary:
    """Normalised salary with annual AUD values."""
    salary_min: Optional[int]
    salary_max: Optional[int]
    confidence: float
    period: Optional[str] = None


class SalaryNormaliser:
    """Normalises parsed salary values to annual AUD."""

    def __init__(self):
        self._use_defaults()

    def _use_defaults(self):
        """Use default annualisation factors."""
        self.hourly_factor = HOURLY_TO_ANNUAL
        self.daily_factor = DAILY_TO_ANNUAL
        self.weekly_factor = WEEKLY_TO_ANNUAL
        self.fortnightly_factor = FORTNIGHTLY_TO_ANNUAL
        self.monthly_factor = MONTHLY_TO_ANNUAL

    def normalise(
        self,
        salary_min: Optional[int],
        salary_max: Optional[int],
        confidence: float,
        period: Optional[str] = None,
    ) -> NormalisedSalary:
        """Normalise salary values to annual AUD.
        
        Args:
            salary_min: Minimum salary value (raw)
            salary_max: Maximum salary value (raw)
            confidence: Parsed confidence level
            period: Time period of salary ('hourly', 'daily', 'weekly', 'fortnightly', 'monthly', 'annual')
            
        Returns:
            NormalisedSalary with annual AUD values
        """
        # Confidence 1.0 and 0.9 are already annual values
        if confidence >= 0.9:
            return NormalisedSalary(
                salary_min=salary_min,
                salary_max=salary_max,
                confidence=confidence,
                period="annual"
            )
        
        # Confidence 0.8 needs annualisation
        if period and confidence >= 0.8:
            return self._annualise(salary_min, salary_max, period)
        
        # Lower confidence values (vague/no salary) remain as-is
        return NormalisedSalary(
            salary_min=salary_min,
            salary_max=salary_max,
            confidence=confidence,
            period=None
        )

    def _annualise(
        self,
        salary_min: Optional[int],
        salary_max: Optional[int],
        period: str,
    ) -> NormalisedSalary:
        """Convert salary to annual based on period."""
        period_lower = period.lower()
        
        if "hour" in period_lower:
            factor = self.hourly_factor
        elif "day" in period_lower:
            factor = self.daily_factor
        elif "week" in period_lower:
            factor = self.weekly_factor
        elif "fortnight" in period_lower:
            factor = self.fortnightly_factor
        elif "month" in period_lower:
            factor = self.monthly_factor
        else:
            # Default to annual - no conversion needed
            return NormalisedSalary(
                salary_min=salary_min,
                salary_max=salary_max,
                confidence=0.8,
                period="annual"
            )
        
        annual_min = salary_min * factor if salary_min else None
        annual_max = salary_max * factor if salary_max else None
        
        return NormalisedSalary(
            salary_min=annual_min,
            salary_max=annual_max,
            confidence=0.8,
            period="annual"
        )

    def annualise_hourly(self, hourly_rate: float) -> int:
        """Convert hourly rate to annual salary."""
        return int(hourly_rate * self.hourly_factor)

    def annualise_daily(self, daily_rate: float) -> int:
        """Convert daily rate to annual salary."""
        return int(daily_rate * self.daily_factor)

    def annualise_weekly(self, weekly_rate: float) -> int:
        """Convert weekly rate to annual salary."""
        return int(weekly_rate * self.weekly_factor)

    def annualise_fortnightly(self, fortnightly_rate: float) -> int:
        """Convert fortnightly rate to annual salary."""
        return int(fortnightly_rate * self.fortnightly_factor)

    def annualise_monthly(self, monthly_rate: float) -> int:
        """Convert monthly rate to annual salary."""
        return int(monthly_rate * self.monthly_factor)


def normalise_salary(
    salary_min: Optional[int],
    salary_max: Optional[int],
    confidence: float,
    period: Optional[str] = None,
) -> NormalisedSalary:
    """Convenience function to normalise salary values.
    
    Args:
        salary_min: Minimum salary value (raw)
        salary_max: Maximum salary value (raw)
        confidence: Parsed confidence level
        period: Time period of salary
        
    Returns:
        NormalisedSalary with annual AUD values
    """
    normaliser = SalaryNormaliser()
    return normaliser.normalise(salary_min, salary_max, confidence, period)