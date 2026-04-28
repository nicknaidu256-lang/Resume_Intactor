# RESUME GENERATION SOP
## Standard Operating Procedure for AI-Assisted Resume Tailoring
### Project: Resume Intactor | Version: 1.0

---

## PURPOSE

This SOP governs how the LLM must generate content to fill the `Master_Resume.docx` template for each job application. Every rule in this document is **mandatory**. The LLM must not deviate from these rules under any circumstances.

---

## CORE PRINCIPLES (NON-NEGOTIABLE)

1. **No Hallucination.** Every fact, skill, metric, job title, employer, qualification, and date must come from `Original_Resume_Master.docx`. If it is not in the original resume, it cannot appear in the output.
2. **No Fabricated Numbers.** Do not invent percentages, dollar figures, timeframes, or improvement metrics unless they appear verbatim in the original resume.
3. **No Content Padding.** Do not generate filler text. If a placeholder cannot be meaningfully filled with real content, leave a note for human review — never fill it with invented content.
4. **The Job Description Informs Keywords Only.** ATS keywords from the JD may be incorporated only if the underlying skill genuinely exists in the original resume. Do not add entirely new skills, tools, or qualifications to match the JD.
5. **Format Compliance is Mandatory.** The template has specific formatting for each section. The LLM must output content that exactly matches the expected format for each placeholder — see Section-by-Section Rules below.
6. **Two-Page Hard Limit.** The final resume must not exceed 2 pages. Every section has a character budget. Stay within it.

---

## INPUTS REQUIRED

Before generating any content, the following inputs MUST be provided:

| Input | Source | Purpose |
|---|---|---|
| `Original_Resume_Master.docx` | `Archive/` | Ground truth for all candidate facts |
| `job_description.txt` | `input/` | ATS keyword source only |

If either input is missing, STOP and request it. Do not generate resume content without both.

---

## PLACEHOLDER MAP

The template contains these placeholders which must be filled:

| Placeholder | Section | Format |
|---|---|---|
| `{{SUMMARY}}` | Professional Summary | Paragraph, ±5% of original char count |
| `{{SKILLS_1}}` | Core Competency 1 body | Pipe-separated skills list |
| `{{SKILLS_2}}` | Core Competency 2 body | Pipe-separated skills list |
| `{{SKILLS_3}}` | Core Competency 3 body | Pipe-separated skills list |
| `{{EXP1_BULLET1}}` | Experience Duty 1 | Single sentence, ≤160 chars |
| `{{EXP1_BULLET2}}` | Experience Duty 2 | Single sentence, ≤160 chars |
| `{{EXP1_BULLET3}}` | Experience Duty 3 | Single sentence, ≤160 chars |
| `{{EXP1_BULLET4}}` | Experience Duty 4 | Single sentence, ≤160 chars |
| `{{EXP1_BULLET5}}` | Experience Duty 5 | Single sentence, ≤160 chars |
| `{{EXP1_BULLET6}}` | Experience Duty 6 | Single sentence, ≤160 chars |
| `{{EXP1_ACH1}}` | Achievement 1 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH2}}` | Achievement 2 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH3}}` | Achievement 3 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH4}}` | Achievement 4 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH5}}` | Achievement 5 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH6}}` | Achievement 6 description | 1–2 sentences, ≤220 chars |
| `{{EXP1_ACH7}}` | Achievement 7 description | 1–2 sentences, ≤220 chars |

**STATIC SECTIONS — DO NOT TOUCH:**
- Header (name, title, contact)
- Career Summary table (all 7 roles and dates)
- Education (both degrees)
- Key Achievement bold subheadings (Capital Program Delivery:, Engineering Leadership:, etc.)

---

## SECTION-BY-SECTION RULES

---

### SECTION 1: PROFESSIONAL SUMMARY — `{{SUMMARY}}`

**Purpose:** A high-impact paragraph that positions the candidate for the specific role.

**Rules:**
- Write exactly 1 paragraph of continuous prose. No bullet points.
- Target character count: **450–530 characters** (±5% of the original 490-char summary).
- Must mention: years of experience, primary domain (pharma/biologics/regulated manufacturing), 2–3 job-specific ATS keywords from the JD.
- Do not change the candidate's actual title, years of experience, or seniority level.
- Open with a strong adjective + role identity (e.g., "Accomplished Engineering Manager...").
- Close with a "seeking" or "poised to" sentence that bridges to the target role.
- Every claim must exist in the original resume.

**Original benchmark (do not copy — use as length/tone reference):**
> "Accomplished Engineering Manager with 10 years of progressive experience delivering complex systems projects, capital programs, and technical leadership across high-assurance, regulated manufacturing environments..."

---

### SECTION 2: CORE COMPETENCIES — `{{SKILLS_1}}`, `{{SKILLS_2}}`, `{{SKILLS_3}}`

**Purpose:** Three rows of competency groups, each with a bold subheading and a pipe-separated skills list.

**Template structure (already in document — DO NOT regenerate the bold labels):**
```
[Bold label already in template]: {{SKILLS_1}}
[Bold label already in template]: {{SKILLS_2}}
[Bold label already in template]: {{SKILLS_3}}
```

**The bold subheading labels in the template are:**
- Row 1: `Engineering Management & Technical Governance:`
- Row 2: `Systems Integration & Technical Delivery:`
- Row 3: `Safety, Quality & Regulatory Assurance:`

**The placeholder value is ONLY the skills list that follows the colon.**

**Rules for each skills list:**
- Format: `Skill 1 │ Skill 2 │ Skill 3 │ Skill 4 │ ...` (use │ as separator, not |)
- Include **6–9 skills** per row.
- All skills must appear in the original resume OR be a direct JD keyword that maps to a real skill in the original.
- Do not invent new skill categories, certifications, or tools not in the original resume.
- Prioritise JD-matching keywords first within each row.
- Character budget per placeholder: **≤280 characters**.

**Original benchmark skills (adapt to JD — use as base):**

`{{SKILLS_1}}` base: `Systems engineering & requirements management │ Team leadership & mentoring │ Major program delivery & cross-functional coordination │ Regulatory compliance (TGA, FDA, EU) │ Design control & configuration management │ Stakeholder & vendor engagement │ Risk & hazard analysis │ Engineering change control`

`{{SKILLS_2}}` base: `End-to-end systems integration │ Equipment specification, validation (IQ/OQ) & commissioning │ FAT/SAT execution │ URS & design review │ Design verification & traceability │ Manufacturing & process engineering │ Utility systems (HVAC, WFI, RO) │ Technical documentation & batch records`

`{{SKILLS_3}}` base: `WHS & machine safety standards │ Regulatory compliance & audit readiness │ Quality Assurance & CAPA processes │ Risk-based engineering reviews & deviation management │ Validation planning & lifecycle documentation │ Budget forecasting & ROI analysis │ Multi-disciplinary collaboration (QA, RA, Operations, Supply Chain)`

---

### SECTION 3: CAREER SUMMARY

**STATIC — DO NOT MODIFY.** All 7 roles, employers, and dates are fixed. Do not add, remove, or edit any entry.

---

### SECTION 4: PROFESSIONAL EXPERIENCE — `{{EXP1_BULLET1}}` to `{{EXP1_BULLET6}}`

**Role in template:** MS&T Process Engineer (Technology Transfer Lead) │ CSL Seqirus │ Jul 2022 – Present

**Purpose:** 6 duty/responsibility bullet points describing the candidate's actual work in this role.

**Rules:**
- Exactly **6 bullets**. No more, no fewer.
- Each bullet = one `{{EXP1_BULLETn}}` placeholder = one sentence.
- Sentences must begin with a strong **action verb** (present tense: Lead, Manage, Direct, Coordinate, Oversee, Facilitate, Execute, etc.)
- Each bullet: **≤160 characters**.
- Content must come from the original resume experience bullets for this role. Rephrase/reorder to match JD keywords.
- Do not fabricate new responsibilities not described in the original.
- Do not repeat the same action verb twice across all 6 bullets.
- Do not include achievements or metrics here — those belong in Key Achievements.
- Do not leave any placeholder empty. If 6 bullets cannot be meaningfully written from the original, consolidate two originals into one and split another to maintain 6.

**Original duties (use as source — adapt wording to JD):**
1. Lead technology transfer and systems integration for vaccine and antivenom platforms, including facility infrastructure and technology upgrades.
2. Direct and coordinate cross-functional teams across engineering, quality, operations, automation, and regulatory functions.
3. Manage requirements traceability, design control, and validation alignment with TGA/FDA/EU regulatory frameworks.
4. Lead capital project planning, risk assessment, and design review coordination across multi-discipline engineering teams.
5. Manage regulatory compliance through risk assessments, hazard analyses, deviation closure, and design change control.
6. Facilitate multi-site and global stakeholder collaboration on systems integration and process scale-up.

---

### SECTION 5: KEY ACHIEVEMENTS — `{{EXP1_ACH1}}` to `{{EXP1_ACH7}}`

**Purpose:** 7 achievement descriptions. The bold subheadings are already printed in the template — the placeholder fills in ONLY the achievement description that follows.

**Bold subheadings already in template (fixed — do not include in placeholder value):**
1. `Capital Program Delivery:`
2. `Engineering Leadership:`
3. `Regulatory Compliance & Technical Governance:`
4. `Vendor Management & Equipment Qualification:`
5. `Process & Documentation` *(note: "Excellence:" is already the start of the placeholder text in this row — start your value from the next word)*
6. `Operational Improvement:`
7. `Cross-Site & Global Collaboration:`

**Special note for `{{EXP1_ACH5}}`:** The template bold label reads "Process & Documentation" and the placeholder begins with the word that follows. Do NOT start your value with "Excellence:" — begin directly with the achievement description.

**Rules:**
- Each value = the description ONLY (after the colon that follows the bold subheading).
- Format: 1–2 sentences of prose. No bullet points inside achievements.
- Character budget: **≤220 characters per placeholder**.
- Content must be grounded in the original resume achievements. Rephrase to align with JD.
- Do not fabricate specific dollar values, percentages, or counts not in the original.
- The one exception: `$800M Project Banksia` is a real figure from the original — it may be retained or referenced.
- Each achievement must be meaningfully distinct from the others — no near-duplicates.

**Original achievement descriptions (use as source — adapt to JD):**
1. Contributed to $800M Project Banksia technology transfer initiatives, coordinating 10+ cross-functional teams from requirements through operational handover.
2. Led multi-stream technical teams; mentored junior engineers in systems thinking, design control, and quality assurance.
3. Delivered GMP-compliant systems under TGA/FDA/EU frameworks; maintained audit-ready documentation and supported regulatory submissions.
4. Executed vendor qualification, FAT/SAT, and equipment commissioning for critical manufacturing and packaging systems.
5. Standardised design control, technical documentation, and risk-based engineering reviews; implemented change control and lifecycle documentation management.
6. Optimised manufacturing design and process parameters, enhancing throughput, uptime, and cost efficiency.
7. Coordinated technology transfer and process scale-up across multiple sites, ensuring scalable, compliant, and reproducible implementation.

---

### SECTION 6: EDUCATION

**STATIC — DO NOT MODIFY.** Both degrees, universities, and dates are fixed.

---

## PAGE LIMIT ENFORCEMENT

The resume must fit within **2 pages**. Use these character budgets to stay within limits:

| Section | Max Characters |
|---|---|
| Professional Summary | 530 |
| Skills Row 1 | 280 |
| Skills Row 2 | 280 |
| Skills Row 3 | 280 |
| Each experience bullet (×6) | 160 each |
| Each achievement description (×7) | 220 each |

**If the generated output would exceed 2 pages:**
1. First, trim experience bullets to ≤130 characters each.
2. Then, trim achievement descriptions to ≤180 characters each.
3. Do not shorten the summary below 420 characters.
4. Never cut bullet count — always maintain 6 bullets and 7 achievements.

---

## ANTI-HALLUCINATION CHECKLIST

Before submitting output, verify every item:

- [ ] Every employer name, job title, and date is from the original resume
- [ ] No new certifications (e.g., PMP, Green Belt) added unless in original
- [ ] No fabricated metrics (%, $, time savings) not in original
- [ ] No FMCG, food manufacturing, printing, packaging industry references (not in candidate's background)
- [ ] No skills or tools invented to match JD keywords
- [ ] All 6 bullets have content (none are empty or placeholder text)
- [ ] All 7 achievement descriptions have content (none are empty or placeholder text)
- [ ] Core competencies respond with skills lists, NOT conversational text
- [ ] No responses like "Please provide..." or "I'm ready to assist..." in any placeholder value

---

## REQUIRED OUTPUT FORMAT

The LLM must return a **JSON object only** with these exact keys. No preamble, no explanation, no markdown code fences.

```json
{
  "SUMMARY": "...",
  "SKILLS_1": "...",
  "SKILLS_2": "...",
  "SKILLS_3": "...",
  "EXP1_BULLET1": "...",
  "EXP1_BULLET2": "...",
  "EXP1_BULLET3": "...",
  "EXP1_BULLET4": "...",
  "EXP1_BULLET5": "...",
  "EXP1_BULLET6": "...",
  "EXP1_ACH1": "...",
  "EXP1_ACH2": "...",
  "EXP1_ACH3": "...",
  "EXP1_ACH4": "...",
  "EXP1_ACH5": "...",
  "EXP1_ACH6": "...",
  "EXP1_ACH7": "..."
}
```

Return ONLY this JSON. Any other text will break the pipeline.

---

## VALIDATION BEFORE WRITING TO TEMPLATE

The `resume_generator.py` script must validate the LLM output before writing:

1. **All 17 keys present** — reject if any key is missing.
2. **No empty strings** — reject if any value is `""` or whitespace only.
3. **No meta-responses** — reject if any value contains "provide", "ready to assist", "please", "I am", "I'm".
4. **Character budgets respected** — warn if any value exceeds its budget (see table above).
5. **No bullet characters in values** — reject if any value starts with `•`, `-`, or `*`. Experience bullets are formatted by the template's Word numbering style, not by the text content.

If validation fails, log the error to `logs/` and prompt the user to retry with corrected inputs, rather than writing a broken resume to `output/`.

---

*SOP Version 1.0 | Project: Resume Intactor | Author: System*
