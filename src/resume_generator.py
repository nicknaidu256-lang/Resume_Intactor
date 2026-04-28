"""
resume_generator.py
Orchestrates the full resume tailoring pipeline:
  1. Load system prompt (prompts/system_prompt.txt)
  2. Load job description (input/job_description.txt)
  3. Call LLM via api_client.generate_text()
  4. Parse and validate JSON response against SOP rules
  5. Write filled template via DocxWriter
  6. Save timestamped output to output/

Entry point: run() — called by main.py
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime

from src.config import config
from src.utils import get_logger, timestamp_string
from src.api_client import generate_text
from src.prompt_builder import load_system_prompt, load_job_description, build_user_message
from src.docx_writer import DocxWriter

logger = get_logger()

# ── SOP Character Budgets ──────────────────────────────────────────────────────
CHAR_BUDGETS = {
    "TITLE":        140,
    "SUMMARY":      530,
    "SKILLS_1":     280,
    "SKILLS_2":     280,
    "SKILLS_3":     280,
    "EXP1_BULLET1": 160,
    "EXP1_BULLET2": 160,
    "EXP1_BULLET3": 160,
    "EXP1_BULLET4": 160,
    "EXP1_BULLET5": 160,
    "EXP1_BULLET6": 160,
    "EXP1_ACH1":    220,
    "EXP1_ACH2":    220,
    "EXP1_ACH3":    220,
    "EXP1_ACH4":    220,
    "EXP1_ACH5":    220,
    "EXP1_ACH6":    220,
    "EXP1_ACH7":    220,
}

REQUIRED_KEYS = list(CHAR_BUDGETS.keys())

# Phrases that mean the LLM ignored the system prompt
META_PHRASES = [
    "please provide",
    "i'm ready",
    "i am ready",
    "ready to assist",
    "could you provide",
    "need the job",
    "need more information",
]

# Bullet characters must NOT start experience bullet values
BULLET_CHARS = ("•", "-", "–", "—", "*", "·")


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_llm_response(raw_text: str) -> dict:
    """Extract and parse JSON from LLM response. Strips markdown fences if present."""
    text = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(
            f"No JSON object found in LLM response.\nRaw response (first 500 chars):\n{raw_text[:500]}"
        )
    return json.loads(text[start:end])


# ── Validation ────────────────────────────────────────────────────────────────

def validate_placeholder_dict(data: dict) -> list:
    """
    Validate LLM output against SOP rules.
    Returns list of error strings. Empty = passed.
    """
    errors = []

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"MISSING KEY: '{key}' not present in LLM output.")

    for key in REQUIRED_KEYS:
        val = str(data.get(key, "")).strip()
        if not val:
            errors.append(f"EMPTY VALUE: '{key}' is blank.")

    # TITLE-specific rules: single line, no bullets, keep concise.
    title = str(data.get("TITLE", "")).strip()
    if title:
        if "\n" in title or "\r" in title:
            errors.append("INVALID VALUE: 'TITLE' must be a single line (no newlines).")
        if title[0] in BULLET_CHARS:
            errors.append("INVALID VALUE: 'TITLE' must not start with a bullet character.")

    for key in REQUIRED_KEYS:
        val_lower = str(data.get(key, "")).lower()
        for phrase in META_PHRASES:
            if phrase in val_lower:
                errors.append(
                    f"META-RESPONSE in '{key}': contains '{phrase}'. "
                    "LLM responded conversationally instead of generating content."
                )
                break

    for i in range(1, 7):
        key = f"EXP1_BULLET{i}"
        val = str(data.get(key, "")).strip()
        if val and val[0] in BULLET_CHARS:
            errors.append(
                f"BULLET CHARACTER in '{key}': starts with '{val[0]}'. "
                "Remove it — the Word template applies bullet formatting automatically."
            )

    for key, budget in CHAR_BUDGETS.items():
        val = str(data.get(key, ""))
        if len(val) > budget:
            logger.warning(
                "OVER BUDGET: '%s' is %d chars (budget %d). May cause page overflow.",
                key, len(val), budget
            )

    return errors


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run() -> Path:
    """
    Full pipeline: prompt → LLM → validate → fill template → save.
    Called by main.py.

    Returns:
        Path to saved output .docx file.

    Raises:
        FileNotFoundError: Missing template, system prompt, or job description.
        ValueError: LLM output fails SOP validation.
        RuntimeError: LLM API call fails.
    """
    project_root = Path(__file__).parent.parent
    prompts_dir = str(project_root / "prompts")
    input_dir = str(project_root / "input")

    # ── Step 1: Load prompts ──────────────────────────────────────────────────
    logger.info("Loading system prompt...")
    system_prompt = load_system_prompt(prompts_dir)
    logger.info("Loading job description...")
    job_description = load_job_description(input_dir)

    # ── Step 2: Build combined prompt ─────────────────────────────────────────
    # Combine system + user into one prompt for compatibility with all LLM backends.
    user_message = build_user_message(job_description)
    full_prompt = f"{system_prompt}\n\n{'═' * 60}\nUSER REQUEST\n{'═' * 60}\n\n{user_message}"

    # ── Step 3: Call LLM ──────────────────────────────────────────────────────
    logger.info("Calling LLM API (max_tokens=2000)...")
    raw_response = generate_text(
        prompt=full_prompt,
        max_tokens=2000,
        temperature=0.3   # Low temperature = more consistent, less hallucination
    )
    logger.info("LLM response received (%d chars). Parsing...", len(raw_response))

    # ── Step 4: Parse JSON ────────────────────────────────────────────────────
    try:
        placeholder_data = parse_llm_response(raw_response)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("JSON parse failed: %s", e)
        logger.debug("Raw LLM response:\n%s", raw_response)
        raise

    # ── Step 5: Validate against SOP ─────────────────────────────────────────
    logger.info("Validating output against SOP rules...")
    errors = validate_placeholder_dict(placeholder_data)
    if errors:
        for err in errors:
            logger.error("  ✗ %s", err)
        raise ValueError(
            f"LLM output failed SOP validation ({len(errors)} error(s)). "
            "See logs for details. Resume not written."
        )
    logger.info("SOP validation passed — all %d placeholders OK.", len(placeholder_data))

    # ── Step 6: Fill template ─────────────────────────────────────────────────
    logger.info("Loading template: %s", config.template_path)
    writer = DocxWriter(config.template_path)

    found = writer.get_section_names()
    logger.info("Template placeholders detected: %s", found)

    missing_in_template = set(REQUIRED_KEYS) - set(found)
    if missing_in_template:
        logger.warning(
            "These placeholders are in SOP but not found in template: %s",
            sorted(missing_in_template)
        )

    writer.replace_placeholders(placeholder_data)

    # ── Step 7: Save output ───────────────────────────────────────────────────
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp_string()
    output_path = output_dir / f"Tailored_Resume_{timestamp}.docx"

    writer.save(output_path)
    logger.info("Resume saved: %s", output_path)

    return output_path
