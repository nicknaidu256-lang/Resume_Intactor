"""
Unit tests for prompt_builder module.
"""

import unittest
from pathlib import Path
from src.prompt_builder import PromptBuilder


class TestPromptBuilder(unittest.TestCase):
    """Test suite for PromptBuilder."""

    @classmethod
    def setUpClass(cls):
        """Create a mock prompts directory with test templates."""
        cls.prompts_dir = Path("tests/test_data/prompts")
        cls.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create simple test templates
        (cls.prompts_dir / "summary_prompt.txt").write_text(
            "Job: {job_title}\nSkills: {required_skills}\nOriginal: {original_summary}"
        )
        (cls.prompts_dir / "bullet_prompt.txt").write_text(
            "Section: {section_name}\nOriginal: {original_bullets}"
        )

    def test_build_summary_prompt(self):
        """Test summary prompt construction."""
        builder = PromptBuilder(self.prompts_dir)
        job_data = {
            "title": "Engineer",
            "company": "TechCo",
            "required_skills": ["Python", "SQL"],
            "keywords": ["backend", "API"]
        }
        original = "Experienced developer with 5 years in Python."

        prompt = builder.build_summary_prompt(job_data, original)

        self.assertIn("Engineer", prompt)
        self.assertIn("Python, SQL", prompt)
        self.assertIn(original, prompt)

    def test_build_bullet_prompt(self):
        """Test bullet prompt construction."""
        builder = PromptBuilder(self.prompts_dir)
        job_data = {
            "required_skills": ["Python"],
            "keywords": ["team", "agile"]
        }
        bullets = ["Built REST API", "Led team of 5"]
        section = "EXP1"

        prompt = builder.build_bullet_prompt(job_data, bullets, section)

        self.assertIn("EXP1", prompt)
        self.assertIn("Built REST API", prompt)
        self.assertIn("• Built REST API", prompt)  # bullets prefixed with •

    def test_fallback_when_template_missing(self):
        """Test fallback prompt generation when templates not found."""
        builder = PromptBuilder(Path("nonexistent"))
        job_data = {"title": "Manager", "company": "Co", "required_skills": [], "keywords": []}
        prompt = builder.build_summary_prompt(job_data, "Original text")
        self.assertIn("Manager", prompt)
        self.assertIn("Original text", prompt)


if __name__ == "__main__":
    unittest.main()
