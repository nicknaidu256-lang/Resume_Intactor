"""
prompt_builder.py
Loads the system prompt and builds the user message for the LLM API call.
The system prompt contains the full candidate profile and all formatting rules.
The user message contains only the job description.
"""

import os


def load_system_prompt(prompts_dir: str) -> str:
    """Load the system prompt from prompts/system_prompt.txt."""
    path = os.path.join(prompts_dir, "system_prompt.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"System prompt not found at {path}. "
            "Ensure prompts/system_prompt.txt exists before running."
        )
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def build_user_message(job_description: str) -> str:
    """
    Wrap the raw job description in a clear instruction block.
    The system prompt already contains the candidate profile and all rules.
    """
    if not job_description or not job_description.strip():
        raise ValueError("Job description is empty. Place job_description.txt in input/ before running.")

    return (
        "Here is the job description for the role I am applying for.\n\n"
        "Please tailor my resume content for this role and return the JSON object "
        "with all 18 placeholders filled. Remember: use only my actual experience "
        "from the candidate profile — do not hallucinate any new facts.\n\n"
        "═══════════════ JOB DESCRIPTION ═══════════════\n\n"
        f"{job_description.strip()}\n\n"
        "═══════════════════════════════════════════════\n\n"
        "Return ONLY valid JSON. No other text before or after the JSON object."
    )


def load_job_description(input_dir: str) -> str:
    """Load job description from input/job_description.txt."""
    path = os.path.join(input_dir, "job_description.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Job description not found at {path}. "
            "Place the job description text in input/job_description.txt before running."
        )
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
