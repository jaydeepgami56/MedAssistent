"""
GenUI Agent - Generative UI agent for dynamic component generation.

Uses LLM to generate React component specifications based on natural language prompts.
Future integration with CopilotKit and MCP for advanced UI generation workflows.
"""

from typing import AsyncIterator
from backend.agents.base_agent import BaseAgent
from backend.llm_client import get_llm_client, LLM_MODEL
import json
import re
import logging
import uuid
import asyncio
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

# ── PPT generation constants ──────────────────────────────────────────────────

# Output base dir — shared bind-mount with the ppt-worker container.
# The ppt-worker writes to /ppt_outputs/{job_id}/ inside the container,
# which maps to PPT_OUTPUT_BASE on the host so the FastAPI backend can serve downloads.
from backend.config import settings as _settings
PPT_OUTPUT_BASE = Path(_settings.PPT_WORKER_OUTPUTS_PATH).resolve()
PPT_OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

PPT_MAX_SLIDES = 20            # hard cap on slides per request

PPT_INTENT_SYSTEM_PROMPT = """You are a presentation planning assistant.
Given a user prompt, output ONLY valid JSON (no markdown, no explanation, no code fences).

Schema:
{
  "slide_count": <integer 1-20>,
  "topic": "<topic string>",
  "style": "corporate" | "minimal" | "bold" | "medical",
  "audience": "<target audience>",
  "color_primary": "<bare 6-char hex — NO # sign>",
  "color_secondary": "<bare 6-char hex — NO # sign>",
  "font_heading": "<font name>",
  "font_body": "<font name>",
  "slides": [
    {
      "index": <1-based integer>,
      "layout": "title" | "content" | "two_column" | "data" | "quote" | "closing",
      "title": "<slide title>",
      "bullets": ["<bullet 1>", "<bullet 2>"],
      "speaker_notes": "<notes>",
      "chart": null | { "type": "BAR" | "LINE" | "PIE", "title": "<chart title>", "data": [{"name": "<series>", "labels": ["<cat1>"], "values": [<n>]}] }
    }
  ]
}

Rules:
- color_primary and color_secondary must be bare hex WITHOUT # (e.g. "0D7377" not "#0D7377")
- slide_count must be between 1 and 20
- Vary layouts — no more than 2 consecutive slides with the same layout
- Choose colors appropriate to the topic, not generic blue unless requested
- Output ONLY the JSON object, nothing else."""


# Singleton instance
_genui_agent = None

GENUI_SYSTEM_PROMPT = """You are a UI component generator. Given a user request, output ONLY valid JSON (no markdown, no explanation, no code fences).

The JSON must follow this exact schema:
{
  "component_type": "card" | "chart" | "table" | "form" | "stat_grid" | "list",
  "title": "string - component title",
  "description": "string - brief description",
  "data": [ ... array of data items ... ],
  "columns": [ ... for tables: array of {key, label} ... ],
  "fields": [ ... for forms: array of {name, label, type} ... ],
  "styling": {
    "accent_color": "#hex color",
    "layout": "grid" | "list" | "single"
  }
}

Examples:

For "weather in new york":
{"component_type":"card","title":"New York Weather","description":"Current weather conditions","data":[{"label":"Temperature","value":"72°F","icon":"🌡️"},{"label":"Condition","value":"Partly Cloudy","icon":"⛅"},{"label":"Humidity","value":"65%","icon":"💧"},{"label":"Wind","value":"12 mph NW","icon":"🌬️"}],"styling":{"accent_color":"#3b82f6","layout":"grid"}}

For "patient list":
{"component_type":"table","title":"Patient Registry","description":"Active patients","columns":[{"key":"name","label":"Name"},{"key":"age","label":"Age"},{"key":"status","label":"Status"}],"data":[{"name":"John Smith","age":"45","status":"Stable"},{"name":"Jane Doe","age":"32","status":"Critical"}],"styling":{"accent_color":"#22c55e","layout":"list"}}

For "vitals dashboard":
{"component_type":"stat_grid","title":"Vital Signs","description":"Current patient vitals","data":[{"label":"Heart Rate","value":"72 bpm","icon":"❤️","color":"#ef4444"},{"label":"SpO2","value":"98%","icon":"🫁","color":"#3b82f6"},{"label":"BP","value":"120/80","icon":"🩸","color":"#f59e0b"}],"styling":{"accent_color":"#a855f7","layout":"grid"}}

Remember: Output ONLY the JSON object. No other text."""


def _extract_response_text(response) -> str:
    """Extract text from LLM response, handling both standard and thinking models."""
    msg = response.choices[0].message
    content = msg.content or ""
    # For thinking models, fall back to reasoning_content if content is empty
    if not content.strip():
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            content = reasoning
    return content.strip()


def _extract_json(text: str) -> dict | None:
    """Extract JSON from text, handling markdown code fences and mixed content."""
    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    # Try extracting from code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try finding first { ... } block
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _build_js_from_plan(slide_plan: dict) -> str:
    """
    Deterministic pptxgenjs JavaScript generator — no LLM involved.

    Takes the structured slide_plan JSON from Phase 1 and produces
    guaranteed-valid JavaScript that the ppt-worker runs with `node generate.js`.

    Handles layouts: title, content, two_column, data (with chart), quote, closing.
    """

    def js_str(s) -> str:
        """Escape a Python string for safe use as a JS double-quoted string literal."""
        s = str(s) if s else ""
        s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
        return f'"{s}"'

    def clean_hex(h: str, default: str = "155E75") -> str:
        """Strip # and normalise to 6 uppercase hex chars."""
        if not h:
            return default
        cleaned = str(h).lstrip("#").upper()
        return cleaned[:6] if len(cleaned) >= 6 else default

    CHART_TYPE_MAP = {"BAR": "bar", "LINE": "line", "PIE": "pie",
                      "bar": "bar", "line": "line", "pie": "pie"}

    primary   = clean_hex(slide_plan.get("color_primary",   ""), "155E75")
    secondary = clean_hex(slide_plan.get("color_secondary", ""), "0C4A5E")
    topic     = slide_plan.get("topic", "Presentation")
    slides    = slide_plan.get("slides", [])

    BG      = "FFFFFF"
    INK     = "1A1A2E"
    MUTED   = "6B7280"
    ACCENT  = primary

    lines = [
        'const pptxgen = require("pptxgenjs");',
        'const pres = new pptxgen();',
        'pres.layout = "LAYOUT_16x9";',
        "",
    ]

    for i, slide in enumerate(slides):
        var    = f"slide{i + 1}"
        layout = slide.get("layout", "content")
        title  = slide.get("title", f"Slide {i + 1}")
        bullets = [b for b in (slide.get("bullets") or []) if b]
        notes   = slide.get("speaker_notes", "")
        chart_d = slide.get("chart")

        lines.append(f"// Slide {i + 1}: {layout}")
        lines.append(f"let {var} = pres.addSlide();")

        if layout == "title" or (i == 0 and layout not in ("quote", "closing")):
            # Full-bleed header slide
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "{ACCENT}" }} }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.5, y: 1.8, w: 9, h: 1.5, fontSize: 40, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri" }});')
            subtitle = bullets[0] if bullets else ""
            if subtitle:
                lines.append(f'{var}.addText({js_str(subtitle)}, {{ x: 0.5, y: 3.5, w: 9, h: 0.8, fontSize: 20, color: "E0F2FE", align: "center", fontFace: "Calibri" }});')
            lines.append(f'{var}.addText({js_str(topic)}, {{ x: 0.5, y: 5.0, w: 9, h: 0.4, fontSize: 12, color: "A5D8F0", align: "center", fontFace: "Calibri" }});')

        elif layout == "closing":
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "{secondary}" }} }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.5, y: 1.8, w: 9, h: 1.5, fontSize: 38, bold: true, color: "FFFFFF", align: "center", fontFace: "Calibri" }});')
            if bullets:
                lines.append(f'{var}.addText({js_str(bullets[0])}, {{ x: 0.5, y: 3.5, w: 9, h: 0.8, fontSize: 20, color: "D1E8F0", align: "center", fontFace: "Calibri" }});')

        elif layout == "quote":
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "F4F1EA" }} }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: 0.12, h: "100%", fill: {{ color: "{ACCENT}" }} }});')
            quote_text = bullets[0] if bullets else title
            lines.append(f'{var}.addText({js_str(quote_text)}, {{ x: 0.6, y: 1.2, w: 8.8, h: 2.8, fontSize: 24, italic: true, color: "{INK}", align: "left", fontFace: "Georgia" }});')
            if len(bullets) > 1:
                lines.append(f'{var}.addText({js_str("— " + bullets[1])}, {{ x: 0.6, y: 4.2, w: 8.8, h: 0.6, fontSize: 14, color: "{ACCENT}", align: "left", fontFace: "Calibri" }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.6, y: 0.2, w: 8.8, h: 0.6, fontSize: 13, color: "{MUTED}", align: "left", fontFace: "Calibri" }});')

        elif layout == "two_column":
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "{BG}" }} }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: 0.08, fill: {{ color: "{ACCENT}" }} }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.5, y: 0.18, w: 9, h: 0.72, fontSize: 26, bold: true, color: "{INK}", fontFace: "Calibri" }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 4.9, y: 1.1, w: 0.05, h: 4.0, fill: {{ color: "E7E2D6" }} }});')
            half = max(1, len(bullets) // 2)
            for col_bullets, x_pos in [(bullets[:half], 0.4), (bullets[half:], 5.2)]:
                if col_bullets:
                    items = ", ".join(
                        f'{{ text: {js_str(b)}, options: {{ bullet: true, fontSize: 16, color: "{INK}", paraSpaceAfter: 10 }} }}'
                        for b in col_bullets
                    )
                    lines.append(f'{var}.addText([{items}], {{ x: {x_pos}, y: 1.2, w: 4.3, h: 3.8 }});')

        elif layout == "data" and chart_d:
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "{BG}" }} }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: 0.08, fill: {{ color: "{ACCENT}" }} }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.5, y: 0.18, w: 9, h: 0.72, fontSize: 26, bold: true, color: "{INK}", fontFace: "Calibri" }});')
            chart_type = CHART_TYPE_MAP.get(chart_d.get("type", "BAR"), "bar")
            chart_title = chart_d.get("title", "")
            series = chart_d.get("data", [])
            if series:
                chart_items = []
                for s in series:
                    sname  = js_str(s.get("name", "Series"))
                    labels = "[" + ", ".join(js_str(str(l)) for l in s.get("labels", [])) + "]"
                    values = "[" + ", ".join(str(v) for v in s.get("values", [])) + "]"
                    chart_items.append(f"{{ name: {sname}, labels: {labels}, values: {values} }}")
                show_title = "true" if chart_title else "false"
                chart_opts = f'{{ x: 0.5, y: 1.1, w: 9, h: 4.4, chartColors: ["{ACCENT}"], title: {js_str(chart_title)}, showTitle: {show_title} }}'
                lines.append(f'{var}.addChart(pres.ChartType.{chart_type}, [{", ".join(chart_items)}], {chart_opts});')
            elif bullets:
                items = ", ".join(
                    f'{{ text: {js_str(b)}, options: {{ bullet: true, fontSize: 18, color: "{INK}", paraSpaceAfter: 10 }} }}'
                    for b in bullets
                )
                lines.append(f'{var}.addText([{items}], {{ x: 0.5, y: 1.25, w: 9, h: 4.1 }});')

        else:
            # Default content layout
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: "100%", fill: {{ color: "{BG}" }} }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0, y: 0, w: "100%", h: 0.08, fill: {{ color: "{ACCENT}" }} }});')
            lines.append(f'{var}.addText({js_str(title)}, {{ x: 0.5, y: 0.18, w: 9, h: 0.72, fontSize: 28, bold: true, color: "{INK}", fontFace: "Calibri" }});')
            lines.append(f'{var}.addShape(pres.ShapeType.rect, {{ x: 0.5, y: 1.05, w: 9, h: 0.04, fill: {{ color: "{ACCENT}" }} }});')
            if bullets:
                items = ", ".join(
                    f'{{ text: {js_str(b)}, options: {{ bullet: true, fontSize: 18, color: "{INK}", paraSpaceAfter: 10 }} }}'
                    for b in bullets
                )
                lines.append(f'{var}.addText([{items}], {{ x: 0.5, y: 1.25, w: 9, h: 4.1 }});')
            else:
                lines.append(f'{var}.addText("(No content)", {{ x: 0.5, y: 1.25, w: 9, h: 4.1, fontSize: 16, color: "{MUTED}", italic: true }});')

        if notes:
            lines.append(f'{var}.addNotes({js_str(notes)});')
        lines.append("")

    lines.append('pres.writeFile({ fileName: "output.pptx" }).then(() => console.log("Done")).catch(e => { console.error(e); process.exit(1); });')
    return "\n".join(lines)



class GenUIAgent(BaseAgent):
    """Agent specialized in generating UI components via natural language."""

    def __init__(self):
        super().__init__(
            agent_id="genui",
            name="GenUI Agent",
            skills=["component_generation", "ui_suggestions", "layout_design", "ppt_generation"],
            models_used=[f"{LLM_MODEL} (LM Studio)"],
            color="#8b5cf6",
            icon="🎨",
            status="Active",
            queue=0
        )
        self.llm_client = get_llm_client()

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """Execute GenUI-specific skills."""
        if skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {skill_name}")

        if skill_name == "component_generation":
            return await self._generate_component(params)
        elif skill_name == "ui_suggestions":
            return await self._suggest_ui_improvements(params)
        elif skill_name == "layout_design":
            return await self._design_layout(params)
        elif skill_name == "ppt_generation":
            return await self._generate_ppt(params)

        raise NotImplementedError(f"Skill {skill_name} not implemented")

    async def _generate_component(self, params: dict) -> dict:
        """Generate UI component specification from prompt."""
        prompt = params.get("prompt", "")

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": GENUI_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048
            )

            response_text = _extract_response_text(response)
            logger.info(f"GenUI raw response ({len(response_text)} chars): {response_text[:200]}")

            component_spec = _extract_json(response_text)

            if component_spec is None:
                component_spec = {
                    "component_type": "card",
                    "title": "Generated Response",
                    "description": prompt,
                    "raw_response": response_text[:1000] if response_text else "Empty response from model",
                    "data": [{"label": "Response", "value": response_text[:200] if response_text else "No content"}],
                    "styling": {"accent_color": "#8b5cf6", "layout": "single"}
                }

        except Exception as e:
            logger.error(f"Error generating component: {str(e)}")
            component_spec = {
                "component_type": "card",
                "title": "Error",
                "description": f"Failed to generate: {str(e)}",
                "data": [{"label": "Error", "value": str(e)}],
                "styling": {"accent_color": "#ef4444", "layout": "single"}
            }

        self.log_audit(prompt, LLM_MODEL, 0.85, "component_generated")

        return {
            "success": True,
            "component": component_spec,
            "prompt": prompt
        }

    async def _suggest_ui_improvements(self, params: dict) -> dict:
        """Suggest improvements for existing UI."""
        return {
            "success": True,
            "suggestions": [
                "Add loading states",
                "Improve accessibility with ARIA labels",
                "Use semantic HTML elements"
            ]
        }

    async def _design_layout(self, params: dict) -> dict:
        """Design responsive layout structure."""
        return {
            "success": True,
            "layout": {
                "type": "grid",
                "columns": 2,
                "responsive": True
            }
        }

    # ── PPT generation pipeline ───────────────────────────────────────────────

    async def _ppt_call_worker(self, job_id: str, js_code: str) -> dict:
        """
        POST js_code to the ppt-worker container.
        Returns { success: bool, thumbnail_count: int, error: str | None }.
        """
        worker_url = f"{_settings.PPT_WORKER_URL}/run"
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(worker_url, json={"job_id": job_id, "js_code": js_code})
            resp.raise_for_status()
            return resp.json()

    async def _generate_ppt(self, params: dict) -> dict:
        """
        Generate a PowerPoint presentation from a natural language prompt.

        Phases:
          1 - LLM intent parse → slide_plan JSON
          2 - Deterministic Python template → generate.js  (no LLM — guaranteed valid)
          3 - ppt-worker container: npm install → node → soffice → pdftoppm
          4 - Build response with download + thumbnail URLs
        """
        prompt = params.get("prompt", "").strip()
        if not prompt:
            return {"success": False, "error": "Prompt is required for ppt_generation"}

        job_id = str(uuid.uuid4())[:8]

        try:
            # ── Phase 1: LLM intent parse ─────────────────────────────────────
            logger.info(f"[PPT:{job_id}] prompt: {prompt}")
            slide_plan = await self._ppt_parse_intent(prompt)
            if slide_plan is None:
                return {"success": False, "error": "Failed to parse presentation intent from prompt.", "job_id": job_id}

            # Reconcile slide_count with the actual slides array length
            actual = len(slide_plan.get("slides", []))
            slide_count = min(actual or int(slide_plan.get("slide_count", 6)), PPT_MAX_SLIDES)
            slide_plan["slide_count"] = slide_count
            slide_plan["slides"] = slide_plan.get("slides", [])[:slide_count]
            logger.info(f"[PPT:{job_id}] plan: {slide_count} slides on '{slide_plan.get('topic', '?')}'")

            # ── Phase 2: deterministic JS generation (no LLM) ────────────────
            js_code = _build_js_from_plan(slide_plan)
            logger.info(f"[PPT:{job_id}] generated {len(js_code)} bytes of JS ({js_code.count('addSlide')} slides)")

            # ── Phase 3: execute via ppt-worker ──────────────────────────────
            try:
                worker_result = await self._ppt_call_worker(job_id, js_code)
            except Exception as http_err:
                return {"success": False, "error": f"ppt-worker unreachable: {http_err}", "job_id": job_id}

            if not worker_result.get("success"):
                return {"success": False, "error": f"ppt-worker failed: {worker_result.get('error', '?')}", "job_id": job_id}

            # ── Phase 4: build response ───────────────────────────────────────
            thumbnail_count = worker_result.get("thumbnail_count", 0)
            thumbnail_urls = [
                f"/agents/genui/ppt/thumbnail/{job_id}/{i}"
                for i in range(1, thumbnail_count + 1)
            ]

            self.log_audit(prompt[:80], LLM_MODEL, 0.90, "ppt_generated")
            logger.info(f"[PPT:{job_id}] done — {slide_count} slides, {thumbnail_count} thumbnails")

            return {
                "success": True,
                "job_id": job_id,
                "topic": slide_plan.get("topic", "Presentation"),
                "slide_count": slide_count,
                "download_url": f"/agents/genui/ppt/download/{job_id}",
                "thumbnail_urls": thumbnail_urls,
                "qa_performed": thumbnail_count > 0,
                "message": f"Generated {slide_count}-slide presentation: {slide_plan.get('topic', prompt[:60])}"
            }

        except Exception as e:
            logger.error(f"[PPT:{job_id}] unexpected error: {e}")
            return {"success": False, "error": f"Internal error: {e}", "job_id": job_id}

    async def _ppt_parse_intent(self, prompt: str) -> dict | None:
        """Phase 1: LLM call → structured slide plan JSON."""
        loop = asyncio.get_event_loop()

        def _call():
            resp = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": PPT_INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4096
            )
            return _extract_response_text(resp)

        try:
            raw = await loop.run_in_executor(None, _call)
            logger.info(f"[PPT INTENT DEBUG] Raw LLM response length: {len(raw)} chars")
            logger.info(f"[PPT INTENT DEBUG] Raw response preview: {raw[:500]}")
            
            plan = _extract_json(raw)
            if plan and "slides" in plan:
                logger.info(f"[PPT INTENT DEBUG] Parsed plan - slide_count field: {plan.get('slide_count')}")
                logger.info(f"[PPT INTENT DEBUG] Parsed plan - actual slides array length: {len(plan.get('slides', []))}")
                logger.info(f"[PPT INTENT DEBUG] Full plan JSON: {json.dumps(plan, indent=2)}")
                return plan
            logger.warning(f"Intent parse returned invalid JSON: {raw[:200]}")
            return None
        except Exception as e:
            logger.error(f"Intent parse error: {e}")
            return None

    async def _ppt_generate_js(self, slide_plan: dict) -> str | None:
        """Phase 2: LLM call → pptxgenjs JavaScript string."""
        loop = asyncio.get_event_loop()
        plan_json = json.dumps(slide_plan, indent=2)

        def _call():
            resp = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": PPT_CODEGEN_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Generate the pptxgenjs JavaScript for this slide plan:\n\n{plan_json}"}
                ],
                temperature=0.2,
                max_tokens=8192
            )
            return _extract_response_text(resp)

        try:
            raw = await loop.run_in_executor(None, _call)
            logger.info(f"[PPT CODEGEN DEBUG] Raw JS response length: {len(raw)} chars")
            
            # Count how many slide variables are generated (let slideN = ...)
            slide_count_in_js = len(re.findall(r'let slide\d+\s*=\s*pres\.addSlide\(\)', raw))
            logger.info(f"[PPT CODEGEN DEBUG] Number of 'pres.addSlide()' calls found: {slide_count_in_js}")
            
            # Strip markdown fences if the model wrapped in them despite instructions
            fence = re.search(r"```(?:javascript|js)?\s*([\s\S]*?)```", raw)
            if fence:
                js_code = fence.group(1).strip()
                logger.info(f"[PPT CODEGEN DEBUG] Extracted JS from code fence, length: {len(js_code)}")
                return js_code
            # Accept bare JS (must start with const/require/var or contain require)
            stripped = raw.strip()
            if stripped and ("require" in stripped or stripped.startswith("const") or stripped.startswith("var")):
                logger.info(f"[PPT CODEGEN DEBUG] Using bare JS output")
                return stripped
            logger.warning(f"JS codegen output does not look like JavaScript: {raw[:200]}")
            return None
        except Exception as e:
            logger.error(f"JS codegen error: {e}")
            return None

    async def _ppt_patch_js_on_error(self, current_js: str, error_msg: str, slide_plan: dict) -> str | None:
        """Ask LLM to fix a generate.js that caused a Node.js error. Returns corrected JS or None."""
        loop = asyncio.get_event_loop()

        def _call():
            resp = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": PPT_CODEGEN_SYSTEM_PROMPT},
                    {"role": "user", "content": (
                        f"The pptxgenjs script below failed with this error:\n\nERROR:\n{error_msg}\n\n"
                        f"SCRIPT:\n{current_js}\n\nFix the error. Output ONLY the corrected JavaScript."
                    )}
                ],
                temperature=0.1,
                max_tokens=8192
            )
            return _extract_response_text(resp)

        try:
            raw = await loop.run_in_executor(None, _call)
            fence = re.search(r"```(?:javascript|js)?\s*([\s\S]*?)```", raw)
            return fence.group(1).strip() if fence else (raw.strip() or None)
        except Exception as e:
            logger.error(f"JS patch error: {e}")
            return None

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """Stream chat responses as JSON component specs (same as playground)."""

        try:
            # When editing, use the existing spec as assistant context + simple user instruction
            if context.get("editing") and context.get("existing_spec"):
                existing_json = json.dumps(context["existing_spec"])
                # Strip "Update ..." prefix from user message if present
                clean_msg = re.sub(r'^Update\s+"[^"]*":\s*', '', message, flags=re.IGNORECASE).strip() or message
                messages = [
                    {"role": "system", "content": GENUI_SYSTEM_PROMPT},
                    {"role": "user", "content": "appointment form"},
                    {"role": "assistant", "content": existing_json},
                    {"role": "user", "content": f"Now modify the JSON above: {clean_msg}. Output ONLY the updated JSON."}
                ]
            else:
                messages = [
                    {"role": "system", "content": GENUI_SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]

            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
                stream=True
            )

            for chunk in response:
                delta = chunk.choices[0].delta
                text = delta.content if delta.content else ""
                # For thinking models, also check reasoning_content
                if not text and hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    text = delta.reasoning_content
                if text:
                    yield text

        except Exception as e:
            logger.error(f"Error in GenUI chat: {str(e)}")
            yield f"[ERROR] {str(e)}"


def get_genui_agent() -> GenUIAgent:
    """Get or create the singleton GenUI agent instance."""
    global _genui_agent
    if _genui_agent is None:
        _genui_agent = GenUIAgent()
        logger.info("GenUI Agent initialized")
    return _genui_agent
