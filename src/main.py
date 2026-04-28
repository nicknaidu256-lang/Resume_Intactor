"""
Main CLI entry point for Resume Tailoring System.
"""

import sys
import argparse
from pathlib import Path

from src.config import config
from src.utils import setup_logging, get_logger
from src.resume_generator import run as run_generator


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ATS Resume Tailoring System - Generate targeted resumes from job descriptions"
    )
    parser.add_argument(
        "--job-file",
        type=Path,
        default=config.job_input_path,
        help=f"Path to job description text file (default: {config.job_input_path})"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.output_dir,
        help=f"Output directory for generated resume (default: {config.output_dir})"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=config.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=f"Logging level (default: {config.log_level})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging (overrides --log-level)"
    )
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else args.log_level
    logger = setup_logging(config.log_path, log_level)

    logger.info("Starting ATS Resume Tailoring System")
    logger.info(f"Project root: {Path(__file__).parent.parent}")
    logger.info(f"AI Engine: Cerebras ({config.cerebras_model}) -> Gemini ({config.gemini_model})")
    logger.info(f"Template: {config.template_path}")
    logger.info(f"Output: {config.output_dir}")

    try:
        output_path = run_generator()
        print(f"\n[OK] Resume generated: {output_path}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\n[ERROR] File not found: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n[ERROR] Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
