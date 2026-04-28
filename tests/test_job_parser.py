"""
Unit tests for job_parser module.
"""

import unittest
from src.job_parser import parse_job_description, JobParser


class TestJobParser(unittest.TestCase):
    """Test suite for JobParser."""

    def setUp(self):
        self.parser = JobParser()

    def test_parse_simple_description(self):
        """Test parsing a simple job description."""
        text = """
        Senior Software Engineer
        at TechCorp Inc.

        Required Skills:
        - Python
        - Django
        - PostgreSQL

        Preferred:
        - Docker
        - AWS

        Responsibilities:
        • Develop backend services
        • Write unit tests
        • Collaborate with team
        """
        result = self.parser.parse(text)

        self.assertEqual(result["title"], "Senior Software Engineer")
        self.assertIn("TechCorp", result["company"])
        self.assertIn("Python", result["required_skills"])
        self.assertIn("PostgreSQL", result["required_skills"])
        self.assertIn("Docker", result["preferred_skills"])
        self.assertIn("Develop backend services", result["responsibilities"])

    def test_extract_title_first_line(self):
        """Test title extraction from first line."""
        lines = ["Data Scientist", "at DataCorp", "", "Requirements:"]
        title = self.parser._extract_title(lines)
        self.assertEqual(title, "Data Scientist")

    def test_extract_company_at_pattern(self):
        """Test company extraction using 'at' pattern."""
        lines = ["Software Engineer", "at Google"]
        company = self.parser._extract_company(lines)
        self.assertIn("Google", company)

    def test_split_required_preferred(self):
        """Test skills splitting logic."""
        skills_text = """Required:
- Python
- SQL

Preferred:
- Kubernetes
- Terraform"""
        required, preferred = self.parser._split_required_preferred(skills_text)
        self.assertIn("Python", required)
        self.assertIn("Kubernetes", preferred)


def parse_test_job():
    """Convenience function for tests."""
    return parse_job_description


if __name__ == "__main__":
    unittest.main()
