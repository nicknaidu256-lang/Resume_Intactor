# Project Bible — Resume Intactor

**Version:** 1.0  
**Last Updated:** April 2026  
**Author:** Abhilash Naidu Paspulati

---

## 1. Project Overview

### 1.1 What is Resume Intactor?

Resume Intactor is an **ATS Resume Tailoring System** that automatically customizes a professional resume for specific job applications. It takes a job description as input, uses a Large Language Model (LLM) to analyze and tailor the content, and produces a polished Word document (.docx) tailored to the target role.

### 1.2 Core Purpose

- Eliminate the manual effort of customizing resumes for each job application
- Ensure resume content is grounded in actual candidate experience (no hallucination)
- Maintain professional formatting and layout integrity
- Produce ATS-friendly output that passes through applicant tracking systems

### 1.3 The Candidate

| Field | Value |
|-------|-------|
| Name | Abhilash Naidu Paspulati |
| Current Title | MS&T Process Engineer (Technology Transfer Lead) |
| Employer | CSL Seqirus |
| Tenure | July 2022 – Present |
| Total Experience | 10 years in GMP pharmaceutical, regulated manufacturing, systems engineering |
| Education | MEng (Manufacturing Engineering), RMIT | BEng Mechanical, JNTU |

---

## 2. Architecture

### 2.1 High-Level Data Flow

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Job Description   │────▶│   Resume Generator  │────▶│  Tailored Resume   │
│  (input/*.txt)      │     │   (Python + LLM)    │     │  (output/*.docx)   │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            ┌──────────────────┐          ┌──────────────────┐
            │   System Prompt  │          │  Master Template │
            │ (prompts/system_ │          │  (templates/*.docx)
            │    prompt.txt)    │          └──────────────────┘
            └──────────────────┘
```

### 2.2 Processing Pipeline

| Step | Component | Purpose |
|------|-----------|---------|
| 1 | `prompt_builder.py` | Load system prompt + JD |
| 2 | `api_client.py` | Call LLM (Cerebras → Gemini) |
| 3 | `resume_generator.py` | Parse JSON, validate against SOP |
| 4 | `docx_writer.py` | Replace placeholders in template |
| 5 | `utils.py` | Save timestamped output |

---

## 3. File Inventory

### 3.1 Source Code (`src/`)

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point |
| `config.py` | Configuration loader (.env) |
| `resume_generator.py` | Orchestrates the full pipeline |
| `api_client.py` | LLM inference (Cerebras → Gemini) |
| `prompt_builder.py` | Loads prompts and builds user message |
| `docx_writer.py` | Word template processor |
| `docx_placeholder_replacer.py` | Run-safe placeholder replacement |
| `job_parser.py` | Job description extractor |
| `utils.py` | Logging, file I/O utilities |

### 3.2 Templates (`templates/`)

| File | Purpose |
|------|---------|
| `Master_Resume.docx` | Word template with 13 placeholders |

### 3.3 Archive (`Archive/`)

| File | Purpose |
|------|---------|
| `Original_Resume_Master.docx` | Source resume (ground truth) |

### 3.4 Prompts (`prompts/`)

| File | Purpose |
|------|---------|
| `system_prompt.txt` | LLM system instructions |
| `RESUME_GENERATION_SOP.md` | Detailed SOP for LLM |

### 3.5 Input/Output

| Directory | Contents |
|-----------|----------|
| `input/` | Job description text files |
| `output/` | Generated resumes (timestamped) |
| `logs/` | Execution logs |

### 3.6 Tests (`tests/`)

| File | Purpose |
|------|---------|
| `test_docx_writer.py` | DOCX writer tests |
| `test_placeholder_replace.py` | Placeholder replacement tests |
| `test_prompt_builder.py` | Prompt builder tests |
| `test_job_parser.py` | Job parser tests |
| `test_docx_output.py` | Output validation |
| `test_table_support.py` | Table handling tests |
| `test_safe_docx_integration.py` | Integration tests |
| `test_advanced_docx_engine.py` | Advanced engine tests |

---

## 4. Configuration

### 4.1 Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `CEREBRAS_API_KEY` | Yes | Primary LLM (Cerebras Cloud) |
| `CEREBRAS_MODEL` | No | Model name (default: `llama3.1-8b`) |
| `GEMINI_API_KEY` | Yes | Fallback LLM (Google Gemini) |
| `GEMINI_MODEL` | No | Model name (default: `gemini-2.5-flash`) |
| `TEMPLATE_PATH` | No | Template location (default: `templates/Master_Resume.docx`) |
| `ORIGINAL_MASTER_PATH` | No | Source resume (default: `Archive/Original_Resume_Master.docx`) |
| `JOB_INPUT_PATH` | No | JD input (default: `input/job_description.txt`) |
| `OUTPUT_DIR` | No | Output directory (default: `output/`) |
| `LOG_PATH` | No | Log file (default: `logs/run.log`) |
| `LOG_LEVEL` | No | Log level (default: `INFO`) |

### 4.2 Path Structure

```
Resume_Intactor/
├── .env                    # API keys
├── src/                    # Application code
│   ├── main.py            # CLI entry
│   ├── config.py         # Configuration
│   ├── resume_generator.py
│   ├── api_client.py
│   ├── prompt_builder.py
│   ├── docx_writer.py
│   ├── docx_placeholder_replacer.py
│   ├── job_parser.py
│   └── utils.py
├── templates/
│   └── Master_Resume.docx # Template with placeholders
├── Archive/
│   └── Original_Resume_Master.docx
├── prompts/
│   ├── system_prompt.txt
│   └── RESUME_GENERATION_SOP.md
├── input/
│   └── job_description.txt
├── output/
└── logs/
    └── run.log
```

---

## 5. The Template

### 5.1 Placeholder Map

| Placeholder | Section | Character Budget |
|-----------|---------|----------------|
| `{{SUMMARY}}` | Professional Summary | 530 |
| `{{SKILLS_1}}` | Core Competencies Row 1 | 280 |
| `{{SKILLS_2}}` | Core Competencies Row 2 | 280 |
| `{{SKILLS_3}}` | Core Competencies Row 3 | 280 |
| `{{EXP1_BULLET1}}` | Experience Duty 1 | 160 |
| `{{EXP1_BULLET2}}` | Experience Duty 2 | 160 |
| `{{EXP1_BULLET3}}` | Experience Duty 3 | 160 |
| `{{EXP1_BULLET4}}` | Experience Duty 4 | 160 |
| `{{EXP1_BULLET5}}` | Experience Duty 5 | 160 |
| `{{EXP1_BULLET6}}` | Experience Duty 6 | 160 |
| `{{EXP1_ACH1}}` | Achievement 1 | 220 |
| `{{EXP1_ACH2}}` | Achievement 2 | 220 |
| `{{EXP1_ACH3}}` | Achievement 3 | 220 |
| `{{EXP1_ACH4}}` | Achievement 4 | 220 |
| `{{EXP1_ACH5}}` | Achievement 5 | 220 |
| `{{EXP1_ACH6}}` | Achievement 6 | 220 |
| `{{EXP1_ACH7}}` | Achievement 7 | 220 |

### 5.2 Static Sections (Not Modified)

- **Header**: Name, title, contact details
- **Career Summary Table**: All 7 roles and dates
- **Education**: Both degrees
- **Achievement Bold Subheadings**: The labels are pre-printed in the template

---

## 6. SOP Rules (Mandatory)

### 6.1 Anti-Hallucination Rules

| Rule | Description |
|------|-------------|
| NO HALLUCINATION | Every fact must come from `Original_Resume_Master.docx` |
| NO FABRICATED NUMBERS | No invented percentages, dollar figures, or metrics |
| NO CONTENT PADDING | No filler text |
| JD KEYWORDS ONLY AS MAPPING | ATS keywords from JD may map to real skills only |

### 6.2 Format Compliance

| Section | Rule |
|---------|------|
| TITLE | Single line, no bullets, max 140 chars |
| SUMMARY | Prose paragraph only, 420–530 chars |
| SKILLS | Pipe-separated (│), no bullets |
| EXP1_BULLET | Single sentence, starts with action verb, no bullet character |
| EXP1_ACH | Prose, no bullet, description only (label already in template) |

### 6.3 Validation

Before writing to template, the pipeline validates:

- [ ] All 17 keys present
- [ ] No empty strings
- [ ] No meta-responses ("please provide", "I'm ready")
- [ ] Character budgets respected
- [ ] No bullet characters in experience bullet values

---

## 7. Usage

### 7.1 Quick Start

```bash
# 1. Edit job description
vim input/job_description.txt

# 2. Run the system
python -m src.main

# 3. Get output
# output/Tailored_Resume_YYYYMMDD_HHMMSS.docx
```

### 7.2 Command-Line Options

```bash
python -m src.main --help

Options:
  --job-file PATH     Job description file (default: input/job_description.txt)
  --output-dir PATH  Output directory (default: output/)
  --log-level LEVEL Logging level: DEBUG, INFO, WARNING, ERROR
  --verbose, -v     Enable debug logging
```

### 7.3 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_docx_writer.py

# Run with verbose output
pytest -v
```

---

## 8. Dependencies

### 8.1 Required Packages

```
python-docx>=1.1.2
python-dotenv>=1.0.1
cerebras-cloud-sdk>=0.1.14
google-genai>=0.11.0
```

### 8.2 Install

```bash
pip install -r requirements.txt
```

---

## 9. API Reference

### 9.1 config.py

```python
from src.config import config

# Access configuration
config.template_path      # Path: templates/Master_Resume.docx
config.cerebras_api_key # str: API key (masked in logs)
config.cerebras_model   # str: "llama3.1-8b"
config.gemini_api_key   # str: API key (masked in logs)
config.gemini_model     # str: "gemini-2.5-flash"
config.output_dir       # Path: output/
config.job_input_path # Path: input/job_description.txt
config.log_level       # str: "INFO"
config.log_path        # Path: logs/run.log
```

### 9.2 resume_generator.py

```python
from src.resume_generator import run, CHAR_BUDGETS, REQUIRED_KEYS

# Execute full pipeline
output_path = run()
# Returns: Path to generated .docx file
# Raises: FileNotFoundError, ValueError, RuntimeError

# Character budgets dict
CHAR_BUDGETS = {
    "TITLE": 140,
    "SUMMARY": 530,
    "SKILLS_1": 280,
    # ... (see Section 5.1)
}

# Required placeholder keys
REQUIRED_KEYS = list(CHAR_BUDGETS.keys())
```

### 9.3 docx_writer.py

```python
from src.docx_writer import DocxWriter

# Initialize with template
writer = DocxWriter("templates/Master_Resume.docx")

# Get list of placeholders
placeholders = writer.get_section_names()
# Returns: List[str] e.g., ["SUMMARY", "SKILLS_1", ...]

# Replace placeholders with data
replaced_count = writer.replace_placeholders({
    "SUMMARY": "Accomplished engineer with 10 years...",
    "SKILLS_1": "Systems engineering │ Team leadership",
    # ...
})
# Returns: int (number of replacements)

# Save to output
writer.save("output/my_resume.docx")
```

### 9.4 prompt_builder.py

```python
from src.prompt_builder import (
    load_system_prompt,
    load_job_description,
    build_user_message,
)

# Load system instructions for LLM
system_prompt = load_system_prompt("prompts")
# Returns: str (full system prompt text)

# Load job description
job_desc = load_job_description("input")
# Returns: str (raw JD text)

# Build user message for API
user_msg = build_user_message(job_desc)
# Returns: str (wrapped JD + instructions)
```

### 9.5 api_client.py

```python
from src.api_client import generate_text

# Generate content via LLM
response = generate_text(
    prompt="Full prompt string",  # System + User combined
    max_tokens=2000,              # Max output tokens
    temperature=0.3,             # Creativity (0.0-1.0)
)
# Returns: str (LLM response text, expected JSON)

# Direct client initialization
from src.api_client import _get_cerebras_client, _get_genai_client
cerebras = _get_cerebras_client()
genai = _get_genai_client()
```

### 9.6 job_parser.py

```python
from src.job_parser import JobParser, parse_job_description

# Parse job description
parser = JobParser()
result = parser.parse(job_description_text)
# Returns: dict with keys:
#   - title: str
#   - company: str
#   - required_skills: List[str]
#   - preferred_skills: List[str]
#   - keywords: List[str]
#   - responsibilities: List[str]
#   - raw_text: str

# Convenience function
result = parse_job_description(text)
```

### 9.7 utils.py

```python
from src.utils import (
    setup_logging,
    get_logger,
    read_text_file,
    write_text_file,
    ensure_dir_exists,
    timestamp_string,
)

# Setup logging
logger = setup_logging(Path("logs/run.log"), "INFO")
# Returns: logging.Logger

# Get configured logger
logger = get_logger()

# Generate timestamp for filenames
ts = timestamp_string()
# Returns: str "20260428_143029"
```

---

## 10. Troubleshooting

### 10.1 Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `CEREBRAS_API_KEY is required` | Missing key in `.env` | Add key to `.env` |
| `GEMINI_API_KEY is required` | Missing fallback key | Add key to `.env` |
| `No placeholders found` | Template missing `{{...}}` | Run `finalize_template.py` |
| `JSON parse failed` | LLM returned invalid JSON | Check prompt, adjust temperature |
| `MISSING KEY: 'TITLE'` | LLM omitted required key | Review SOP, regenerate |
| `EMPTY VALUE: 'SUMMARY'` | LLM left placeholder blank | Regenerate with corrected prompt |
| `BULLET CHARACTER in 'EXP1_BULLET1'` | LLM added bullet char | Regenerate |
| `OVER BUDGET: 'SUMMARY' is 600 chars` | Content too long | Regenerate with shorter content |

### 10.2 Debugging Guide

#### Enable Debug Logging

```bash
python -m src.main --verbose
# or
LOG_LEVEL=DEBUG python -m src.main
```

#### Check Template Placeholders

```bash
python -c "from src.docx_writer import scan_template; from pathlib import Path; print(scan_template(Path('templates/Master_Resume.docx')))"
```

#### Validate Job Description

```bash
python -c "from src.prompt_builder import load_job_description; print(load_job_description('input')[:500])"
```

#### Test LLM Connection

```bash
python -c "from src.api_client import generate_text; print(generate_text('Say OK', 10, 0.1))"
```

#### Inspect Output Document

```bash
python -c "from docx import Document; d = Document('output/Tailored_Resume_20260428.docx'); print([p.text for p in d.paragraphs][:10])"
```

### 10.3 Log Analysis

Logs are written to `logs/run.log`. Enable debug logging to see:

- Placeholder detection counts
- LLM API call details
- JSON parsing steps
- Replacement statistics
- Character count warnings

```bash
tail -f logs/run.log
```

---

## 11. Advanced Topics

### 11.1 LLM Fallback Chain

```
1. Try Cerebras (llama3.1-8b → llama-3.3-70b → llama-3.1-70b)
2. If Cerebras fails → Fall back to Gemini (gemini-2.5-flash)
3. If both fail → Raise RuntimeError
```

The fallback is automatic and logged. Check logs for: "Cerebras unavailable — falling back to Gemini."

### 11.2 Run-Safe Replacement

The `docx_placeholder_replacer.py` module ensures:

- Placeholders split across multiple Word runs are handled correctly
- All run formatting (bold, italic, colors) is preserved
- Table cells and nested structures work correctly
- Merged cells (gridSpan) are handled correctly

### 11.3 Character Budget Enforcement

Each placeholder has a strict character limit to ensure the resume fits on 2 pages. The generator warns but does not block if limits are exceeded.

| Section | Hard Limit |
|---------|-----------|
| SUMMARY | 530 (warns above 500) |
| SKILLS rows | 280 |
| EXP1_BULLET | 160 |
| EXP1_ACH | 220 |

### 11.4 Adding New Placeholders

1. Add placeholder to `Master_Resume.docx` in Word
2. Add key to `CHAR_BUDGETS` in `resume_generator.py`
3. Add to REQUIRED_KEYS list
4. Run test to verify replacement works

### 11.5 Switching LLM Models

Edit `.env`:

```bash
CEREBRAS_MODEL=llama-3.3-70b
# or
GEMINI_MODEL=gemini-2.0-flash-exp
```

---

## 12. Project History

### 12.1 Development Timeline

| Date | Milestone |
|------|----------|
| 2025 | Initial implementation |
| 2026 | DOCX engine refinement |
| 2026 | Safe placeholder replacer (run-safe) |
| 2026 | Gemini fallback integration |
| 2026 | Template finalization with 13 placeholders |

### 12.2 Key Reports

| Report | Description |
|--------|-------------|
| `FINAL_DELIVERY_REPORT.md` | Final delivery documentation |
| `IMPLEMENTATION_REPORT.md` | Initial implementation details |
| `SAFE_DOCX_ENGINE_IMPLEMENTATION.md` | DOCX engine refinement |
| `AI_LAYER_REFACTOR_REPORT.md` | LLM layer changes |
| `FINAL_REPORT.md` | Comprehensive project report |

---

## 13. Contact & Credits

| Item | Details |
|------|---------|
| Developer | Abhilash Naidu Paspulati |
| Primary LLM | Cerebras (llama models) |
| Fallback LLM | Google Gemini |
| Framework | python-docx |
| Project Home | `C:\Users\abhil\Project_A\Resume_Intactor` |

---

## 14. Quick Reference Card

| Command | Action |
|---------|--------|
| `python -m src.main` | Generate resume |
| `python -m src.main --verbose` | Debug mode |
| `python -m src.main --job-file custom.txt` | Custom JD file |
| `pytest` | Run tests |
| `pytest -v` | Verbose tests |
| `pytest tests/test_docx_writer.py` | Specific test |

---

*End of Project Bible*