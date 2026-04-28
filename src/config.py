"""
Configuration loader for the Resume Tailoring System.
Loads settings from .env file and provides typed access.
Simplified: only Cerebras (primary) and Gemini (fallback) supported.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Config:
    """Application configuration."""
    # LLM API keys
    cerebras_api_key: str
    cerebras_model: str
    gemini_api_key: str
    gemini_model: str

    # Paths (relative to project root)
    template_path: Path
    original_master_path: Path
    job_input_path: Path
    output_dir: Path
    log_path: Path

    # Logging
    log_level: str
    debug: bool

    def __init__(self):
        """Load and validate configuration."""
        # Cerebras settings (primary)
        self.cerebras_api_key = os.getenv("CEREBRAS_API_KEY", "").strip()
        self.cerebras_model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")

        # Gemini settings (fallback)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Paths
        self.template_path = PROJECT_ROOT / os.getenv("TEMPLATE_PATH", "templates/Master_Resume.docx")
        self.original_master_path = PROJECT_ROOT / os.getenv("ORIGINAL_MASTER_PATH", "Archive/Original_Resume_Master.docx")
        self.job_input_path = PROJECT_ROOT / os.getenv("JOB_INPUT_PATH", "input/job_description.txt")
        self.output_dir = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output/")
        self.log_path = PROJECT_ROOT / os.getenv("LOG_PATH", "logs/run.log")

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # Validate: both API keys must be set
        if not self.cerebras_api_key:
            raise ValueError("CEREBRAS_API_KEY is required in .env")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required in .env (fallback)")


# Global config instance
config = Config()
