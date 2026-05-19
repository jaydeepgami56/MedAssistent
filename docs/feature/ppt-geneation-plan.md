# PPT Generation — Option 1 Implementation Plan
### AI Agent + Container Architecture (Claude + pptxgenjs)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Breakdown](#component-breakdown)
4. [Task Plan](#task-plan)
5. [File Structure](#file-structure)
6. [API & Data Flow](#api--data-flow)
7. [QA Pipeline](#qa-pipeline)
8. [Dependencies](#dependencies)
9. [Common Pitfalls & Mitigations](#common-pitfalls--mitigations)
10. [Acceptance Criteria](#acceptance-criteria)

---

## Overview

This plan details how to implement an AI-powered PowerPoint generation system using a **server-side container** approach. Claude (the AI agent) orchestrates the entire pipeline: interpreting the user's prompt, generating slide content, writing JavaScript code, executing it in a sandboxed Linux container via `pptxgenjs`, performing visual QA, and delivering a downloadable `.pptx` file.

**Key principles:**
- All generation happens server-side — no browser dependency
- Real `.pptx` output that opens natively in PowerPoint, Google Slides, LibreOffice
- Visual QA loop before delivery — no broken slides shipped
- Modular pipeline — each stage is independent and testable

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│              (claude.ai chat / API consumer)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │  User prompt: "Make a 6-slide deck on X"
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CLAUDE AI AGENT                            │
│                                                                 │
│  1. Intent parsing   →  What slides? What style? What data?     │
│  2. Skill loading    →  Read /mnt/skills/public/pptx/SKILL.md   │
│  3. Content gen      →  Titles, bullets, speaker notes          │
│  4. Code generation  →  JavaScript using pptxgenjs API          │
│  5. QA orchestration →  Inspect images, fix issues, re-run      │
└──────────────┬──────────────────────────────────────────────────┘
               │  bash_tool / create_file / str_replace
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LINUX CONTAINER (Ubuntu 24)                  │
│                                                                 │
│  /home/claude/          ← working directory (scratchpad)        │
│  /mnt/user-data/outputs ← final deliverables (user-visible)    │
│  /mnt/skills/public/    ← read-only skill files                 │
│                                                                 │
│  Tools available:                                               │
│    node / npm           ← JavaScript runtime                    │
│    pptxgenjs            ← .pptx generation library              │
│    LibreOffice (soffice) ← .pptx → .pdf conversion             │
│    pdftoppm             ← .pdf → .jpg slide images              │
│    python3 + Pillow     ← thumbnail grids, image processing     │
│    sharp                ← icon rasterization (SVG → PNG)        │
│    react-icons          ← icon library                          │
└──────────────┬──────────────────────────────────────────────────┘
               │  output.pptx → copy to outputs/
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DELIVERY LAYER                              │
│   present_files tool → user gets download link in chat          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Skill Loader
- **Purpose:** Loads `SKILL.md` and `pptxgenjs.md` before any code is written
- **Why:** Encodes environment-specific constraints, API quirks, and design rules that override general training data
- **Input:** File path `/mnt/skills/public/pptx/SKILL.md`
- **Output:** Active constraints in context (color rules, layout limits, pitfall list)

### 2. Intent Parser (Claude reasoning)
- **Purpose:** Extracts structured intent from the user's natural language prompt
- **Extracts:**
  - Number of slides
  - Topic / domain
  - Requested style (corporate, minimal, bold, etc.)
  - Any data to visualize (tables, charts)
  - Target audience
  - Color preferences or brand constraints

### 3. Content Generator (Claude reasoning)
- **Purpose:** Produces slide-by-slide content plan before touching any code
- **Output per slide:**
  - Slide type (`title`, `content`, `two-column`, `data`, `quote`, `closing`)
  - Title text
  - Body bullets / paragraphs
  - Speaker notes
  - Visual element suggestion (chart type, icon, image hint)
  - Color palette assignment

### 4. Code Generator (Claude writing JS)
- **Purpose:** Translates the content plan into executable `pptxgenjs` JavaScript
- **Responsibilities:**
  - Instantiate `pptxgen()` with correct layout (`LAYOUT_16x9`)
  - Define slide master(s) for consistent branding
  - Add each slide with precise coordinate-based layout
  - Embed charts natively via `addChart()`
  - Rasterize icons via `sharp` + `react-icons`
  - Avoid all known pitfalls (no `#` in hex, fresh shadow objects, no unicode bullets)
- **Output:** `/home/claude/generate.js`

### 5. Execution Engine (bash_tool)
- **Purpose:** Runs the generated JavaScript in the container
- **Commands:**
  ```bash
  cd /home/claude
  npm install pptxgenjs react react-dom react-icons sharp
  node generate.js
  ```
- **Success signal:** `output.pptx` exists with non-zero file size
- **Failure handling:** Parse Node.js error → patch code → re-run (max 3 retries)

### 6. Visual QA Engine
- **Purpose:** Detect user-visible defects before delivery
- **Pipeline:**
  ```bash
  python scripts/office/soffice.py --headless --convert-to pdf output.pptx
  rm -f slide-*.jpg
  pdftoppm -jpeg -r 150 output.pdf slide
  ls -1 "$PWD"/slide-*.jpg
  ```
- **Checks (per slide):**
  - Text overflow / clipping at box boundaries
  - Overlapping elements (text through shapes, stacked labels)
  - Insufficient margins (< 0.5" from slide edges)
  - Low-contrast text
  - Leftover placeholder text (`XXX`, `lorem`, `TODO`, `[insert]`)
  - Columns/cards misaligned
- **Output:** List of defects per slide number

### 7. Fix Loop
- **Purpose:** Apply targeted fixes to `generate.js` for any QA-detected issues
- **Tool:** `str_replace` for surgical edits — never rewrite the whole file for a small fix
- **Limit:** Max 1 fix-and-verify cycle per run; sub-pixel cosmetic issues are skipped
- **Re-render:** After fixes, re-run the full conversion pipeline before re-inspecting

### 8. Delivery
- **Purpose:** Move final file to user-accessible location and surface it
- **Commands:**
  ```bash
  cp /home/claude/output.pptx /mnt/user-data/outputs/presentation.pptx
  ```
- **Tool:** `present_files(["/mnt/user-data/outputs/presentation.pptx"])`

---

## Task Plan

### Phase 0 — Setup (Pre-generation)

| # | Task | Tool | Notes |
|---|------|------|-------|
| 0.1 | Load `SKILL.md` | `view` | Required before any code |
| 0.2 | Load `pptxgenjs.md` | `view` | API reference + pitfall list |
| 0.3 | Parse user intent | Claude reasoning | Extract slide count, topic, style |

### Phase 1 — Content Planning

| # | Task | Tool | Notes |
|---|------|------|-------|
| 1.1 | Choose color palette | Claude reasoning | Match topic, not generic blue |
| 1.2 | Select font pairing | Claude reasoning | Header + body fonts |
| 1.3 | Plan slide layouts | Claude reasoning | Vary layouts, no repeated structure |
| 1.4 | Write slide content | Claude reasoning | Title, bullets, notes per slide |
| 1.5 | Identify visual elements | Claude reasoning | Charts, icons, images per slide |

### Phase 2 — Code Generation

| # | Task | Tool | Notes |
|---|------|------|-------|
| 2.1 | Create `generate.js` scaffold | `create_file` | pptxgen init, layout, author |
| 2.2 | Define slide master(s) | Inline in JS | Background, font defaults |
| 2.3 | Add title slide | Inline in JS | Dark background, logo area |
| 2.4 | Add content slides (N slides) | Inline in JS | One slide per plan entry |
| 2.5 | Add charts (if any) | Inline in JS | Native `addChart()` — not images |
| 2.6 | Add icon assets | Inline in JS | `sharp` + `react-icons` pipeline |
| 2.7 | Add closing slide | Inline in JS | Call-to-action or summary |
| 2.8 | Write file call | Inline in JS | `pres.writeFile({ fileName: "output.pptx" })` |

### Phase 3 — Execution

| # | Task | Tool | Notes |
|---|------|------|-------|
| 3.1 | Install dependencies | `bash_tool` | `npm install pptxgenjs react react-dom react-icons sharp` |
| 3.2 | Run generator | `bash_tool` | `node generate.js` |
| 3.3 | Verify file exists | `bash_tool` | `ls -lh output.pptx` |
| 3.4 | Handle errors (if any) | `str_replace` + retry | Max 3 attempts |

### Phase 4 — Visual QA

| # | Task | Tool | Notes |
|---|------|------|-------|
| 4.1 | Convert .pptx → PDF | `bash_tool` | Via LibreOffice soffice |
| 4.2 | Convert PDF → slide images | `bash_tool` | `pdftoppm -jpeg -r 150` |
| 4.3 | List slide images | `bash_tool` | Capture absolute paths |
| 4.4 | Inspect each slide image | `view` | Check for visual defects |
| 4.5 | Check for placeholder text | `bash_tool` | `extract-text output.pptx \| grep -iE "xxx\|lorem\|TODO"` |
| 4.6 | Log defects found | Claude reasoning | Prioritize user-visible only |

### Phase 5 — Fix & Re-verify (if needed)

| # | Task | Tool | Notes |
|---|------|------|-------|
| 5.1 | Apply fixes to `generate.js` | `str_replace` | Surgical edits only |
| 5.2 | Re-run generator | `bash_tool` | `node generate.js` |
| 5.3 | Re-run full QA pipeline | `bash_tool` + `view` | All 4 bash commands |
| 5.4 | Stop after one cycle | — | No looping on cosmetic issues |

### Phase 6 — Delivery

| # | Task | Tool | Notes |
|---|------|------|-------|
| 6.1 | Copy to outputs directory | `bash_tool` | `cp output.pptx /mnt/user-data/outputs/` |
| 6.2 | Present file to user | `present_files` | With short summary — no postamble |

---

## File Structure

```
/home/claude/                        ← container working directory
│
├── generate.js                      ← main pptxgenjs script
├── output.pptx                      ← generated presentation
├── output.pdf                       ← intermediate (QA only)
├── slide-1.jpg                      ← QA slide images
├── slide-2.jpg
├── slide-N.jpg
│
└── assets/                          ← optional
    ├── logo.png
    └── background.jpg

/mnt/user-data/outputs/
└── presentation.pptx                ← final file (user-downloadable)

/mnt/skills/public/pptx/
├── SKILL.md                         ← read-only, loaded first
├── pptxgenjs.md                     ← API reference
└── editing.md                       ← template editing guide
```

---

## API & Data Flow

```
User prompt
    │
    ▼
Claude parses intent
    │
    ├─── slide_count: 6
    ├─── topic: "Product Roadmap Q3"
    ├─── style: "corporate minimal"
    └─── data: [{ chart: "bar", values: [...] }]
    │
    ▼
Content plan (per slide)
    │
    ├── slide 1: { type: "title", title: "Q3 Roadmap", subtitle: "..." }
    ├── slide 2: { type: "content", title: "Goals", bullets: [...] }
    ├── slide 3: { type: "two-column", left: [...], right: [...] }
    ├── slide 4: { type: "data", chart: "BAR", data: [...] }
    ├── slide 5: { type: "quote", quote: "...", author: "..." }
    └── slide 6: { type: "closing", cta: "Next Steps" }
    │
    ▼
generate.js (pptxgenjs)
    │
    ├── pres.layout = 'LAYOUT_16x9'
    ├── pres.defineSlideMaster({ ... })
    │
    ├── slide 1 → addShape + addText (title layout)
    ├── slide 2 → addText with bullet array
    ├── slide 3 → two addShape columns + text
    ├── slide 4 → addChart(pres.charts.BAR, data, options)
    ├── slide 5 → addShape (quote block) + addText
    └── slide 6 → addShape + addText (closing)
    │
    ▼
node generate.js → output.pptx
    │
    ▼
LibreOffice → output.pdf → pdftoppm → slide-N.jpg
    │
    ▼
Visual inspection → defects? → fix → re-run
    │
    ▼
output.pptx → /mnt/user-data/outputs/ → present_files
```

---

## QA Pipeline

### Automated Content Check

```bash
# Extract all text from slides
extract-text output.pptx

# Check for placeholder leftovers
extract-text output.pptx | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|this.*(page|slide).*layout"
```

### Visual Inspection Prompt (used when viewing slide images)

```
Visually inspect these slides for user-visible defects.

Look for:
- Overlapping elements (text through shapes, lines through words)
- Text overflow or cut off at edges/box boundaries
- Elements too close (< 0.3" gaps) or nearly touching
- Uneven spacing or cramped sections
- Insufficient margin from slide edges (< 0.5")
- Low-contrast text (light on light, dark on dark)
- Leftover placeholder content
- Columns not aligned consistently

For each slide, list user-visible issues only.
Skip sub-pixel positioning and cosmetic nitpicks.
```

### Fix Decision Matrix

| Defect | Severity | Action |
|--------|----------|--------|
| Text overflow / clipping | Critical | Fix immediately |
| Overlapping elements | Critical | Fix immediately |
| Missing content | Critical | Fix immediately |
| Low contrast text | High | Fix in first cycle |
| Misaligned columns | High | Fix in first cycle |
| Minor spacing (< 5px) | Low | Skip |
| Sub-pixel cosmetic | None | Skip |

---

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `pptxgenjs` | Core .pptx generation | `npm install -g pptxgenjs` |
| `react` + `react-dom` | Icon rendering | `npm install -g react react-dom` |
| `react-icons` | Icon library (FA, MD, HI, BI) | `npm install -g react-icons` |
| `sharp` | SVG → PNG rasterization | `npm install -g sharp` |
| LibreOffice (`soffice`) | .pptx → .pdf (QA) | Pre-installed in container |
| `pdftoppm` (Poppler) | .pdf → .jpg slides (QA) | Pre-installed in container |
| `python3` + `Pillow` | Thumbnail grids | `pip install Pillow --break-system-packages` |

**One-liner install:**
```bash
npm install -g pptxgenjs react react-dom react-icons sharp
pip install Pillow --break-system-packages
```

---

## Common Pitfalls & Mitigations

| Pitfall | Problem | Mitigation |
|---------|---------|------------|
| `color: "#FF0000"` | File corruption | Always use bare hex: `"FF0000"` |
| 8-char hex opacity (`"00000020"`) | File corruption | Use `opacity: 0.12` property |
| Reusing shadow objects | Second shape corrupted | Use factory function `makeShadow()` |
| Unicode bullets `"•"` | Double bullets rendered | Use `bullet: true` in options |
| `lineSpacing` with bullets | Excessive gaps | Use `paraSpaceAfter` instead |
| `ROUNDED_RECTANGLE` + accent bar | Corners not covered | Use `RECTANGLE` for both |
| Chart as PNG/image | Loses editability | Use native `addChart()` |
| `position: fixed` in QA viewer | Not applicable (bash env) | N/A |
| Stale slide images after fix | Inspecting old output | Always re-run all 4 QA commands after fix |

---

## Acceptance Criteria

A generated presentation is considered **complete and ready for delivery** when all of the following are true:

- [ ] `.pptx` file exists and has non-zero size
- [ ] File opens without errors in PowerPoint / Google Slides / LibreOffice
- [ ] No text is clipped, overflowing, or cut off at box boundaries
- [ ] No unintended element overlaps (text through shapes, labels on arrows)
- [ ] All slides have at least 0.5" margin from slide edges
- [ ] No placeholder text remains (`XXX`, `lorem`, `TODO`, `[insert]`)
- [ ] All content from the plan is present and in correct order
- [ ] Color contrast is sufficient — no light-on-light or dark-on-dark text
- [ ] Charts (if any) are native pptxgenjs charts, not PNG images
- [ ] File is copied to `/mnt/user-data/outputs/` and presented via `present_files`

---

*Last updated: May 2026 | Claude Sonnet 4.6 | Environment: Ubuntu 24 container*