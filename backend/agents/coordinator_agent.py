"""
Coordinator Agent - Message routing, multi-agent consensus, and safety checks.

Routes incoming messages to appropriate specialist agents, orchestrates
multi-agent consensus for complex cases, enforces safety checks (confidence
thresholds, critical flags), and triggers escalation alerts for ESI 1-2 and
critical findings.
"""

import logging
import json
from typing import AsyncIterator
from anthropic import Anthropic

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted coordination — requires clinician verification"


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent for message routing and multi-agent orchestration.

    Routes incoming messages to the correct specialist agent(s), builds
    consensus from multiple agents, enforces safety checks, and triggers
    escalation for critical cases.
    """

    def __init__(self, anthropic_api_key: str):
        """
        Initialize Coordinator Agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude reasoning
        """
        super().__init__(
            agent_id="coordinator",
            name="Coordinator Agent",
            skills=[
                "agent_routing",
                "consensus",
                "safety_check",
                "escalation"
            ],
            models_used=["Claude API"],
            color="#e879f9",  # Purple/Fuchsia
            icon="🧠",
            status="Active",
            queue=0
        )

        self.anthropic_client = Anthropic(api_key=anthropic_api_key)

        # Registry of specialist agents - will be populated after initialization
        self.specialist_agents = {}

    def register_specialist(self, agent_id: str, agent) -> None:
        """
        Register a specialist agent for routing.

        Args:
            agent_id: Agent identifier (e.g., "triage", "radiology")
            agent: Agent instance implementing BaseAgent
        """
        self.specialist_agents[agent_id] = agent
        logger.info(f"Registered specialist agent: {agent_id}")

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute coordinator skill with given parameters.

        Args:
            skill_name: Name of skill to execute
            params: Skill parameters

        Returns:
            dict: Skill execution result

        Raises:
            ValueError: If skill_name not in self.skills
        """
        if skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {skill_name}. Valid skills: {self.skills}")

        if skill_name == "agent_routing":
            return await self._agent_routing(params)
        elif skill_name == "consensus":
            return await self._consensus(params)
        elif skill_name == "safety_check":
            return await self._safety_check(params)
        elif skill_name == "escalation":
            return await self._escalation(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _agent_routing(self, params: dict) -> dict:
        """
        Analyze message and determine which specialist agent(s) to invoke.

        Uses Claude to analyze the user's intent and select the appropriate
        specialist agent(s) based on message content, keywords, and context.

        Args:
            params: dict with keys:
                - message (str): User message to analyze
                - context (dict, optional): Additional context (patient data, history)

        Returns:
            dict with keys:
                - target_agents (list[str]): List of agent IDs to invoke
                - reasoning (str): Explanation of routing decision
                - confidence (float): Confidence in routing decision (0.0-1.0)
                - requires_consensus (bool): Whether multiple agents need consensus
                - disclaimer (str): Safety disclaimer
        """
        try:
            message = params.get("message", "")
            context = params.get("context", {})

            # Build list of available agents
            available_agents = [
                {"id": "triage", "capabilities": "ESI scoring, red flag detection, patient routing, emergency assessment"},
                {"id": "radiology", "capabilities": "X-ray/CT/MRI analysis, imaging report generation, pathology detection"},
                {"id": "diagnostic", "capabilities": "Differential diagnosis, test recommendations, pattern recognition, rare diseases"},
                {"id": "pharmacy", "capabilities": "Drug interactions, dosage calculations, contraindications, allergy checks"},
                {"id": "monitoring", "capabilities": "Vital signs tracking, MEWS scoring, anomaly detection, trend analysis"},
                {"id": "documentation", "capabilities": "SOAP notes, discharge summaries, ICD-10 coding, clinical documentation"},
                {"id": "research", "capabilities": "PubMed search, clinical guidelines, evidence synthesis, trial matching"}
            ]

            # Build prompt for Claude
            prompt = f"""You are a medical coordination specialist. Analyze this message and determine which specialist agent(s) should handle it.

MESSAGE: {message}

CONTEXT: {json.dumps(context) if context else "None"}

AVAILABLE AGENTS:
{chr(10).join(f"- {agent['id']}: {agent['capabilities']}" for agent in available_agents)}

ROUTING RULES:
1. Single agent for straightforward requests (e.g., "analyze this X-ray" → radiology)
2. Multiple agents for complex cases requiring different expertise (e.g., "patient with chest pain and abnormal ECG" → triage + radiology + diagnostic)
3. Triage should be invoked for any emergency/urgent assessment
4. Research should be invoked when clinical evidence or guidelines are needed
5. Documentation should be invoked for note generation or coding tasks

Provide your routing decision as a JSON object with:
- target_agents (list[str]): Agent IDs to invoke (e.g., ["triage", "radiology"])
- reasoning (str): Explanation of why these agents were selected
- confidence (float 0.0-1.0): Your confidence in this routing decision
- requires_consensus (bool): True if multiple agents need to reach consensus

Return ONLY valid JSON."""

            # Call Claude API
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            content = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # Validate target_agents are available
            target_agents = result.get("target_agents", [])
            available_agent_ids = [agent["id"] for agent in available_agents]
            invalid_agents = [agent for agent in target_agents if agent not in available_agent_ids]

            if invalid_agents:
                logger.warning(f"Invalid agents in routing result: {invalid_agents}. Removing them.")
                result["target_agents"] = [agent for agent in target_agents if agent in available_agent_ids]

            # Add disclaimer
            result["disclaimer"] = DISCLAIMER

            # Log audit trail
            self.log_audit(
                request=f"Routing: {message[:50]}",
                model="Claude API",
                confidence=result.get("confidence", 0.0),
                action=f"Routed to {', '.join(result['target_agents'])}"
            )

            return result

        except Exception as e:
            logger.error(f"Agent routing failed: {e}")
            return {
                "error": str(e),
                "target_agents": [],
                "reasoning": "Routing failed - defaulting to manual selection",
                "confidence": 0.0,
                "requires_consensus": False,
                "disclaimer": DISCLAIMER
            }

    async def _consensus(self, params: dict) -> dict:
        """
        Build consensus from multiple agent results.

        Analyzes outputs from multiple specialist agents, identifies agreement
        and disagreement, and builds a combined report. Flags disagreements
        for human review.

        Args:
            params: dict with keys:
                - agent_results (list[dict]): Results from multiple agents
                    Each dict should have: agent_id, output, confidence
                - question (str, optional): Original question/request

        Returns:
            dict with keys:
                - consensus_report (str): Combined findings from all agents
                - agreement_level (str): "full", "partial", "conflicting"
                - agreements (list[str]): Points where agents agree
                - disagreements (list[dict]): Points where agents disagree
                    Each dict: {"topic": str, "agent_views": [{agent_id, view, confidence}]}
                - requires_review (bool): True if disagreements exist
                - confidence (float): Overall confidence (minimum of all agents)
                - disclaimer (str): Safety disclaimer
        """
        try:
            agent_results = params.get("agent_results", [])
            question = params.get("question", "")

            if not agent_results:
                return {
                    "error": "No agent results provided",
                    "consensus_report": "",
                    "agreement_level": "none",
                    "agreements": [],
                    "disagreements": [],
                    "requires_review": True,
                    "confidence": 0.0,
                    "disclaimer": DISCLAIMER
                }

            # Build summary of all agent results
            agent_summaries = []
            for result in agent_results:
                agent_id = result.get("agent_id", "unknown")
                output = result.get("output", {})
                confidence = result.get("confidence", 0.0)

                agent_summaries.append(f"**{agent_id.upper()}** (confidence: {confidence:.2f}):\n{json.dumps(output, indent=2)}")

            # Use Claude to analyze consensus
            prompt = f"""You are a medical coordination specialist. Analyze these outputs from multiple specialist agents and build a consensus report.

ORIGINAL QUESTION: {question}

AGENT OUTPUTS:
{chr(10).join(agent_summaries)}

TASKS:
1. Identify points where agents AGREE
2. Identify points where agents DISAGREE or provide conflicting information
3. Build a combined consensus report synthesizing all findings
4. Determine agreement level: "full" (all agents agree), "partial" (some agreement/disagreement), "conflicting" (major disagreements)

Provide your analysis as a JSON object with:
- consensus_report (str): Comprehensive report combining all agent findings
- agreement_level (str): "full", "partial", or "conflicting"
- agreements (list[str]): Key points where all agents agree
- disagreements (list[dict]): Points of disagreement, each with:
    - topic (str): What they disagree about
    - agent_views (list[dict]): Each agent's view with {{"agent_id": str, "view": str, "confidence": float}}
- requires_review (bool): True if any disagreements exist or any confidence < 0.7

Return ONLY valid JSON."""

            # Call Claude API
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            content = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # Calculate overall confidence (minimum of all agents)
            confidences = [r.get("confidence", 0.0) for r in agent_results]
            overall_confidence = min(confidences) if confidences else 0.0
            result["confidence"] = overall_confidence

            # Force requires_review if any confidence < 0.7
            if overall_confidence < 0.7:
                result["requires_review"] = True

            # Add disclaimer
            result["disclaimer"] = DISCLAIMER

            # Log audit trail
            self.log_audit(
                request=f"Consensus for {len(agent_results)} agents",
                model="Claude API",
                confidence=overall_confidence,
                action=f"Agreement: {result['agreement_level']}, Review: {result['requires_review']}"
            )

            return result

        except Exception as e:
            logger.error(f"Consensus building failed: {e}")
            return {
                "error": str(e),
                "consensus_report": "Consensus analysis failed",
                "agreement_level": "unknown",
                "agreements": [],
                "disagreements": [],
                "requires_review": True,
                "confidence": 0.0,
                "disclaimer": DISCLAIMER
            }

    async def _safety_check(self, params: dict) -> dict:
        """
        Verify safety constraints: confidence > 0.7, critical flags, escalation rules.

        Enforces safety rules across all agent outputs:
        - Confidence threshold (> 0.7 required for approval)
        - Critical flags (ESI 1-2, critical drug interactions, MEWS >= 5, SpO2 < 90%)
        - Mandatory escalation for life-threatening findings

        Args:
            params: dict with keys:
                - agent_result (dict): Agent result to check
                    Should include: confidence, output with potential flags
                - agent_id (str): Which agent generated this result

        Returns:
            dict with keys:
                - passed (bool): True if all safety checks passed
                - failures (list[str]): List of failed safety checks
                - requires_escalation (bool): True if escalation needed
                - requires_review (bool): True if human review required
                - action (str): Recommended action ("approve", "review", "escalate")
                - disclaimer (str): Safety disclaimer
        """
        try:
            agent_result = params.get("agent_result", {})
            agent_id = params.get("agent_id", "unknown")

            failures = []
            requires_escalation = False
            requires_review = False

            # Extract key fields from result
            confidence = agent_result.get("confidence", 0.0)
            output = agent_result.get("output", {})

            # SAFETY CHECK 1: Confidence threshold
            if confidence < 0.7:
                failures.append(f"Confidence too low: {confidence:.2f} < 0.7 (mandatory human review)")
                requires_review = True

            # SAFETY CHECK 2: ESI 1-2 (for triage results)
            if agent_id == "triage":
                esi_score = output.get("esi_score")
                if esi_score is not None and esi_score <= 2:
                    failures.append(f"ESI-{esi_score} detected (automatic escalation to attending physician)")
                    requires_escalation = True

            # SAFETY CHECK 3: Critical drug interactions (for pharmacy results)
            if agent_id == "pharmacy":
                interactions = output.get("interactions", [])
                critical_interactions = [i for i in interactions if i.get("severity") == "critical"]
                if critical_interactions:
                    failures.append(f"{len(critical_interactions)} critical drug interaction(s) detected (workflow blocked until physician override)")
                    requires_escalation = True

            # SAFETY CHECK 4: MEWS >= 5 (for monitoring results)
            if agent_id == "monitoring":
                mews_score = output.get("mews_score")
                if mews_score is not None and mews_score >= 5:
                    failures.append(f"MEWS score {mews_score} >= 5 (automatic attending notification)")
                    requires_escalation = True

            # SAFETY CHECK 5: SpO2 < 90% (critical vital sign)
            vitals = output.get("vitals", {})
            spo2 = vitals.get("spo2")
            if spo2 is not None and spo2 < 90:
                failures.append(f"Critical SpO2: {spo2}% < 90% (immediate alert)")
                requires_escalation = True

            # SAFETY CHECK 6: Red flags from any agent
            red_flags = output.get("red_flags", [])
            if red_flags:
                failures.append(f"{len(red_flags)} red flag(s) detected: {', '.join(red_flags[:3])}")
                requires_review = True

            # Determine action
            if requires_escalation:
                action = "escalate"
            elif requires_review or failures:
                action = "review"
            else:
                action = "approve"

            passed = len(failures) == 0

            result = {
                "passed": passed,
                "failures": failures,
                "requires_escalation": requires_escalation,
                "requires_review": requires_review,
                "action": action,
                "disclaimer": DISCLAIMER
            }

            # Log audit trail
            self.log_audit(
                request=f"Safety check for {agent_id}",
                model="Rule-based",
                confidence=confidence,
                action=f"{action.upper()}: {len(failures)} failure(s)"
            )

            return result

        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {
                "error": str(e),
                "passed": False,
                "failures": [f"Safety check error: {str(e)}"],
                "requires_escalation": True,
                "requires_review": True,
                "action": "review",
                "disclaimer": DISCLAIMER
            }

    async def _escalation(self, params: dict) -> dict:
        """
        Trigger escalation alert for attending physician.

        Logs and triggers alert for critical findings (ESI 1-2, critical drug
        interactions, MEWS >= 5, SpO2 < 90%, or other life-threatening conditions).

        Args:
            params: dict with keys:
                - reason (str): Reason for escalation
                - agent_id (str): Which agent triggered escalation
                - patient_id (str, optional): Patient identifier
                - severity (str, optional): "critical" or "urgent" (default: "urgent")
                - details (dict, optional): Additional details for alert

        Returns:
            dict with keys:
                - alert_triggered (bool): True if alert was triggered
                - alert_id (str): Unique alert identifier (timestamp-based)
                - notify_roles (list[str]): Roles to notify
                - message (str): Alert message
                - severity (str): Alert severity level
                - timestamp (str): ISO timestamp
                - disclaimer (str): Safety disclaimer
        """
        try:
            from datetime import datetime

            reason = params.get("reason", "Unspecified escalation")
            agent_id = params.get("agent_id", "unknown")
            patient_id = params.get("patient_id", "Unknown")
            severity = params.get("severity", "urgent")
            details = params.get("details", {})

            # Generate alert ID
            timestamp = datetime.utcnow()
            alert_id = f"ALERT-{timestamp.strftime('%Y%m%d-%H%M%S')}"

            # Determine who to notify based on severity and reason
            notify_roles = ["Attending Physician", "Charge Nurse"]

            # Add specialty-specific notifications
            reason_lower = reason.lower()
            if "cardiac" in reason_lower or "chest pain" in reason_lower or "esi-1" in reason_lower:
                notify_roles.append("Cardiology")
            if "drug interaction" in reason_lower or "contraindication" in reason_lower:
                notify_roles.append("Pharmacy")
            if "respiratory" in reason_lower or "spo2" in reason_lower:
                notify_roles.append("Respiratory Therapy")

            # Build alert message
            message = f"{severity.upper()} ALERT [{alert_id}]: {reason}"
            if patient_id != "Unknown":
                message += f" | Patient: {patient_id}"
            message += f" | Source: {agent_id}"

            # Log escalation (in production, this would trigger actual notifications)
            logger.warning(f"[ESCALATION] {message}")
            logger.warning(f"[ESCALATION] Notify: {', '.join(notify_roles)}")
            logger.warning(f"[ESCALATION] Details: {json.dumps(details)}")

            result = {
                "alert_triggered": True,
                "alert_id": alert_id,
                "notify_roles": notify_roles,
                "message": message,
                "severity": severity,
                "timestamp": timestamp.isoformat(),
                "disclaimer": DISCLAIMER
            }

            # Log audit trail
            self.log_audit(
                request=f"Escalation: {reason[:50]}",
                model="Escalation system",
                confidence=1.0,  # Escalations are definitive
                action=f"ALERT triggered: {alert_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Escalation failed: {e}")
            return {
                "error": str(e),
                "alert_triggered": False,
                "alert_id": "",
                "notify_roles": [],
                "message": "Escalation system error",
                "severity": "unknown",
                "timestamp": "",
                "disclaimer": DISCLAIMER
            }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses about coordination and routing.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        # Build coordinator-specific system prompt
        system_prompt = f"""You are the coordination specialist for the MedAssist AI platform.

Your role:
- Route incoming requests to the appropriate specialist agents
- Orchestrate multi-agent consensus for complex cases
- Enforce safety checks and escalation rules
- Coordinate between different specialists
- NEVER provide clinical advice directly (delegate to specialists)
- ALWAYS include disclaimer: "{DISCLAIMER}"

Available specialists:
- Triage (ESI scoring, emergency assessment)
- Radiology (imaging analysis)
- Diagnostic (differential diagnosis)
- Pharmacy (drug interactions, dosage)
- Monitoring (vitals, MEWS scoring)
- Documentation (SOAP notes, coding)
- Research (PubMed, guidelines)

Context:
- Current conversation: {context.get('conversation_id', 'Unknown')}
- Previous routing: {context.get('previous_routing', 'None')}

Respond concisely and professionally."""

        # Stream response from Claude
        with self.anthropic_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        ) as stream:
            for text in stream.text_stream:
                yield text

        # Yield disclaimer at the end
        yield f"\n\n{DISCLAIMER}"


# Global agent instance
_coordinator_agent = None


def init_coordinator_agent(anthropic_api_key: str) -> None:
    """
    Initialize global Coordinator Agent.

    Args:
        anthropic_api_key: Anthropic API key for Claude
    """
    global _coordinator_agent
    try:
        _coordinator_agent = CoordinatorAgent(anthropic_api_key)
        logger.info("Coordinator Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Coordinator Agent: {e}")
        _coordinator_agent = None


def get_coordinator_agent() -> CoordinatorAgent:
    """
    Get the global Coordinator Agent instance.

    Returns:
        CoordinatorAgent or None if not initialized
    """
    return _coordinator_agent
