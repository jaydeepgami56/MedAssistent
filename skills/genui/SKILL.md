# GenUI Skill

## When to Use

Activate for any request involving UI component generation, layout design, or presentation creation.

**Triggers (component_generation):** "generate", "create component", "show me a", "build a form",
"dashboard", "table", "chart", "card", "layout", "UI for", "widget", "display"

**Triggers (ppt_generation):** "presentation", "PowerPoint", "slide deck", "PPT",
"make slides", "create a deck", "slide show", "generate slides", "deck on", "slides about",
"slideshow", "slides for", "pptx"

**Triggers (ui_suggestions):** "improve", "suggest", "how to make better", "UX advice",
"accessibility", "what should I change"

**Triggers (layout_design):** "layout", "arrange", "structure", "grid", "how to organize"

---

## Process

### component_generation

1. PARSE prompt for component type: card, table, form, stat_grid, list, or chart
2. GENERATE JSON spec matching the component schema (component_type, title, description, data, styling)
3. RETURN spec for A2UI canvas rendering

### ui_suggestions

1. ANALYZE described UI component or existing spec
2. IDENTIFY up to 5 improvements (accessibility, loading states, contrast, hierarchy)
3. RETURN ranked suggestion list

### layout_design

1. PARSE layout requirements (number of items, relationships, screen size)
2. RECOMMEND grid/list/single layout with column count and responsive breakpoints
3. RETURN layout spec

### ppt_generation

#### Phase 0 — Setup & Validation
1. VERIFY node runtime is available via subprocess `which node`
2. CHECK for optional QA tools: `soffice` (LibreOffice), `pdftoppm` (Poppler)
3. LOG tool availability; continue without QA tools if only soffice/pdftoppm are missing
4. FAIL fast with clear error if `node` is absent

#### Phase 1 — Intent Parsing
1. PARSE user prompt via LLM to extract:
   - `slide_count` (integer, max 20)
   - `topic` (string)
   - `style` ("corporate" | "minimal" | "bold" | "medical")
   - `audience` (string — staff, patients, executives, etc.)
   - `color_primary` / `color_secondary` (bare 6-char hex, NO `#` prefix)
   - `font_heading` / `font_body`
   - Per-slide: `layout`, `title`, `bullets[]`, `speaker_notes`, optional `chart`
2. ENFORCE: slide_count ≤ 20; reject and error if exceeded
3. CHOOSE color palette appropriate to topic — avoid generic blue unless explicitly requested

#### Phase 2 — Code Generation
1. GENERATE `generate.js` via LLM using the slide plan JSON
2. ENFORCE pptxgenjs rules (see Safety Rules below)
3. WRITE the JavaScript to `{work_dir}/generate.js`

#### Phase 3 — Execution
1. RUN `npm install pptxgenjs` in work_dir (local install, no global permissions needed)
2. RUN `node generate.js` from work_dir CWD
3. VERIFY `output.pptx` exists in work_dir with non-zero file size
4. ON ERROR: parse Node.js stderr, ask LLM to patch generate.js, retry (max 3 attempts)

#### Phase 4 — Visual QA (skipped if soffice/pdftoppm absent)
1. CONVERT output.pptx → PDF: `soffice --headless --convert-to pdf output.pptx`
2. CONVERT PDF → JPG slides: `pdftoppm -jpeg -r 150 output.pdf slide`
3. COLLECT all slide-N.jpg files sorted by slide number

#### Phase 5 — Fix Loop (max 1 cycle; skipped if text-only LLM)
1. INSPECT each slide image for user-visible defects:
   - Text overflow / clipping at box boundaries (Critical)
   - Overlapping elements — text through shapes, labels on arrows (Critical)
   - Missing content from the plan (Critical)
   - Leftover placeholder text: XXX, lorem, TODO, [insert] (Critical)
   - Low-contrast text — light-on-light, dark-on-dark (High)
   - Misaligned columns or cards (High)
   - Elements within 0.5" of slide edges (High)
   - Minor spacing < 5px (Skip)
   - Sub-pixel cosmetic issues (Skip)
2. APPLY surgical fixes to generate.js for Critical/High defects only
3. RE-RUN Phase 3 + Phase 4 once; stop regardless of remaining issues

#### Phase 6 — Delivery
1. COPY output.pptx to persistent output directory keyed by job_id
2. COPY slide-N.jpg thumbnails to thumbnail directory keyed by job_id
3. RETURN: `{ job_id, topic, slide_count, download_url, thumbnail_urls[], qa_performed }`
4. DELETE work_dir temp directory in `finally` block

---

## Models Used

- **LM Studio / configured LLM** (via `LLM_MODEL`): Intent parsing, content planning, JS code generation, QA analysis (text-only; vision QA requires multimodal upgrade)
- **pptxgenjs** (Node.js npm package): .pptx file generation — native format, opens in PowerPoint/Google Slides/LibreOffice
- **LibreOffice soffice**: .pptx → .pdf conversion (QA pipeline only)
- **pdftoppm** (Poppler): .pdf → .jpg slide thumbnails

---

## A2UI Output Format

**Full-screen "Slides" view** in the frontend (GenUI agent, `#8b5cf6` violet accent):

```
Header: "Slide Deck Generator" + slide count badge
Prompt card: textarea + Generate button + 4 medical quick chips
Loading card: phase indicator text + indeterminate progress bar
─────────────────────────────────────────────────────────────
Ready to download bar (green):   [Download .pptx]
3-column thumbnail grid (16:9 aspect ratio per cell):
  ┌────────┐  ┌────────┐  ┌────────┐
  │[1] img │  │[2] img │  │[3] img │
  └────────┘  └────────┘  └────────┘
─────────────────────────────────────────────────────────────
⚠ AI-GENERATED SLIDES — REVIEW BEFORE USE IN CLINICAL SETTINGS
```

Fallback: if QA tools absent, shows placeholder grid of 16:9 boxes with slide numbers.

**API endpoints**:
- `POST /agents/genui/ppt` — trigger pipeline
- `GET /agents/genui/ppt/download/{job_id}` — download .pptx (FileResponse)
- `GET /agents/genui/ppt/thumbnail/{job_id}/{n}` — slide thumbnail .jpg (FileResponse)

---

## Safety Rules

- NEVER include patient PHI in generated presentations (PHI stays local via LM Studio; do not pass to cloud LLMs)
- ALWAYS log job_id, prompt summary, model used, and outcome to audit trail via `log_audit()`
- ALWAYS include disclaimer on all output: "AI-generated — requires review before use in clinical settings"
- TIMEOUT: Kill any subprocess after 120 seconds; return error with clear message
- CLEANUP: Delete temp work_dir in `finally` block after every run (success or failure)
- MAX SLIDES: Reject requests for more than 20 slides with HTTP 400 before processing
- FAIL FAST: If `node` is not installed, return immediate error — do not attempt fallback

### pptxgenjs Code Rules (non-negotiable — enforced in PPT_CODEGEN_SYSTEM_PROMPT)

| Rule | Wrong | Correct |
|---|---|---|
| Hex colors | `"#8B5CF6"` | `"8B5CF6"` (no `#`) |
| Transparency | `"8B5CF620"` (8-char hex) | `{ color: "8B5CF6", transparency: 20 }` |
| Shadow objects | Reuse same object | `function makeShadow() { return {...} }` factory |
| Bullets | `"• item"` (unicode) | `{ text: "item", options: { bullet: true } }` |
| Paragraph spacing | `lineSpacing` with bullets | `paraSpaceAfter` |
| Rounded shapes | `"roundRect"` + accent bar | `"rect"` for both |
| Charts | `addImage()` of chart PNG | `pres.addChart()` with native data |
| File write | `pres.writeFile("output")` | `pres.writeFile({ fileName: "output.pptx" })` |

---

## Example

**Input prompt:** "Create a 6-slide deck on antibiotic stewardship principles for hospital staff"

**Parsed intent:**
```json
{
  "slide_count": 6,
  "topic": "Antibiotic Stewardship Principles",
  "style": "medical",
  "audience": "hospital staff",
  "color_primary": "0D7377",
  "color_secondary": "F2A65A",
  "font_heading": "Calibri",
  "font_body": "Calibri"
}
```

**Output slides:**
1. Title — "Antibiotic Stewardship: Principles for Clinical Practice"
2. Content — "What is Antibiotic Stewardship?" (4 bullets)
3. Two-column — "Broad-Spectrum vs. Targeted Therapy"
4. Data — Bar chart: Resistance rates by antibiotic class (native `addChart()`)
5. Content — "De-escalation Protocol" (step list)
6. Closing — "Key Takeaways + Resources"

**Delivered as:** `presentation.pptx` — opens natively in PowerPoint, Google Slides, LibreOffice
