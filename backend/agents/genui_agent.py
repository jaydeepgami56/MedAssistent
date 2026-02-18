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

logger = logging.getLogger(__name__)

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


class GenUIAgent(BaseAgent):
    """Agent specialized in generating UI components via natural language."""

    def __init__(self):
        super().__init__(
            agent_id="genui",
            name="GenUI Agent",
            skills=["component_generation", "ui_suggestions", "layout_design"],
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
