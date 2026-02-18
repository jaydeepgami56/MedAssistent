"""
Triage Agent - ESI scoring, red flag detection, and patient routing.

Implements Emergency Severity Index (ESI) 1-5 scoring with comprehensive
red flag detection for cardiac, respiratory, neurological, trauma, and other
life-threatening conditions. Uses ClinicalBERT for entity extraction and
Claude API for clinical reasoning.
"""

import logging
from typing import AsyncIterator
from backend.llm_client import get_llm_client, LLM_MODEL

from backend.agents.base_agent import BaseAgent
from backend.models.clinical_bert import get_clinical_bert_service

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted triage — requires clinician verification"


class TriageAgent(BaseAgent):
    """
    Triage Agent for emergency patient assessment.

    Provides ESI 1-5 scoring, red flag detection, and routing recommendations
    for incoming patients. Uses ClinicalBERT for symptom extraction and MedGemma 27B
    via LM Studio for clinical reasoning.
    """

    def __init__(self):
        """
        Initialize Triage Agent.
        """
        super().__init__(
            agent_id="triage",
            name="Triage Agent",
            skills=[
                "esi_scoring",
                "red_flag_detection",
                "patient_routing",
                "emergency_alert"
            ],
            models_used=["ClinicalBERT", "MedGemma 27B (LM Studio)"],
            color="#ef4444",  # Red
            icon="🚨",
            status="Active",
            queue=0
        )

        self.llm_client = get_llm_client()

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute triage skill with given parameters.

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

        if skill_name == "esi_scoring":
            return await self._esi_scoring(params)
        elif skill_name == "red_flag_detection":
            return await self._red_flag_detection(params)
        elif skill_name == "patient_routing":
            return await self._patient_routing(params)
        elif skill_name == "emergency_alert":
            return await self._emergency_alert(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _esi_scoring(self, params: dict) -> dict:
        """
        Perform ESI scoring with red flag detection.

        Args:
            params: dict with keys:
                - complaint (str): Chief complaint
                - vitals (dict): hr, bp_sys, bp_dia, spo2, temp, rr
                - pain_scale (int): 1-10
                - duration (str): Symptom duration
                - history (str): Medical history
                - allergies (list): Allergies
                - medications (list): Current medications

        Returns:
            dict with keys:
                - esi_score (int): 1-5
                - esi_label (str): e.g. "ESI-1 Resuscitation"
                - red_flags (list): List of detected red flags
                - routing (str): Department recommendation
                - wait_time (str): Estimated wait time
                - reasoning (str): Clinical reasoning chain
                - confidence (float): 0.0-1.0
                - disclaimer (str): Safety disclaimer
        """
        # Extract parameters
        complaint = params.get("complaint", "")
        vitals = params.get("vitals", {})
        pain_scale = params.get("pain_scale", 0)
        duration = params.get("duration", "")
        history = params.get("history", "")
        allergies = params.get("allergies", [])
        medications = params.get("medications", [])

        # Build full clinical text for entity extraction
        clinical_text = f"""
        Chief complaint: {complaint}
        Duration: {duration}
        Medical history: {history}
        Current medications: {', '.join(medications) if medications else 'None'}
        Allergies: {', '.join(allergies) if allergies else 'None'}
        Pain scale: {pain_scale}/10
        """

        # Extract entities using ClinicalBERT
        entities = {"symptoms": [], "conditions": [], "medications": [],
                   "allergies": [], "anatomical_locations": [], "temporal_indicators": []}

        clinical_bert = get_clinical_bert_service()
        if clinical_bert:
            try:
                entities = clinical_bert.extract_entities(clinical_text)
                logger.info(f"Extracted entities: {entities}")
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")

        # Detect red flags
        red_flags = self._detect_red_flags(
            complaint=complaint,
            vitals=vitals,
            entities=entities,
            pain_scale=pain_scale
        )

        # Determine minimum ESI based on red flags
        minimum_esi = 2 if red_flags else 5

        # Use MedGemma 27B via LM Studio for ESI determination with clinical reasoning
        esi_result = await self._llm_esi_determination(
            complaint=complaint,
            vitals=vitals,
            pain_scale=pain_scale,
            duration=duration,
            history=history,
            entities=entities,
            red_flags=red_flags,
            minimum_esi=minimum_esi
        )

        # Add disclaimer
        esi_result["disclaimer"] = DISCLAIMER

        # Log audit trail
        self.log_audit(
            request=f"ESI scoring: {complaint[:50]}",
            model="ClinicalBERT + MedGemma 27B",
            confidence=esi_result.get("confidence", 0.0),
            action=f"ESI-{esi_result['esi_score']} assigned"
        )

        return esi_result

    def _detect_red_flags(
        self,
        complaint: str,
        vitals: dict,
        entities: dict,
        pain_scale: int
    ) -> list[str]:
        """
        Detect life-threatening red flags.

        Args:
            complaint: Chief complaint text
            vitals: Vital signs dict
            entities: Extracted medical entities
            pain_scale: Pain scale 1-10

        Returns:
            list: Detected red flags
        """
        red_flags = []
        complaint_lower = complaint.lower()
        symptoms = [s.lower() for s in entities.get("symptoms", [])]
        conditions = [c.lower() for c in entities.get("conditions", [])]

        # CARDIAC red flags
        cardiac_keywords = ["chest pain", "palpitations", "syncope", "cardiac arrest",
                           "crushing pain", "chest pressure", "radiating pain"]
        if any(kw in complaint_lower or kw in ' '.join(symptoms) for kw in cardiac_keywords):
            red_flags.append("Cardiac: chest pain/cardiac symptoms")

        # RESPIRATORY red flags
        respiratory_keywords = ["dyspnea", "shortness of breath", "stridor",
                               "respiratory arrest", "can't breathe", "difficulty breathing"]
        if any(kw in complaint_lower or kw in ' '.join(symptoms) for kw in respiratory_keywords):
            red_flags.append("Respiratory: dyspnea/respiratory distress")

        # SpO2 < 90%
        spo2 = vitals.get("spo2", 100)
        if spo2 < 90:
            red_flags.append(f"Respiratory: SpO2 < 90% (SpO2 = {spo2}%)")

        # NEUROLOGICAL red flags
        neuro_keywords = ["altered consciousness", "stroke", "seizure", "unconscious",
                         "confused", "unresponsive", "weakness", "facial droop", "slurred speech"]
        if any(kw in complaint_lower or kw in ' '.join(symptoms) for kw in neuro_keywords):
            red_flags.append("Neurological: altered consciousness/stroke signs")

        # GCS < 9 (if provided in vitals)
        gcs = vitals.get("gcs", 15)
        if gcs < 9:
            red_flags.append(f"Neurological: GCS < 9 (GCS = {gcs})")

        # TRAUMA red flags
        trauma_keywords = ["hemorrhage", "bleeding", "burn", "trauma", "injury",
                          "accident", "fall", "gunshot", "stabbing"]
        if any(kw in complaint_lower or kw in ' '.join(symptoms) for kw in trauma_keywords):
            red_flags.append("Trauma: hemorrhage/burns/mechanism of injury")

        # OTHER life-threatening conditions
        other_keywords = ["anaphylaxis", "sepsis", "overdose", "pregnant", "labor",
                         "allergic reaction", "swelling", "hives"]
        if any(kw in complaint_lower or kw in ' '.join(symptoms) for kw in other_keywords):
            red_flags.append("Other: anaphylaxis/sepsis/overdose/obstetric emergency")

        # Vital sign abnormalities
        hr = vitals.get("hr", 80)
        bp_sys = vitals.get("bp_sys", 120)
        bp_dia = vitals.get("bp_dia", 80)
        temp = vitals.get("temp", 37.0)
        rr = vitals.get("rr", 16)

        # Tachycardia or bradycardia
        if hr > 120 or hr < 50:
            red_flags.append(f"Vital sign: abnormal HR ({hr} bpm)")

        # Hypotension or hypertension
        if bp_sys < 90 or bp_sys > 180:
            red_flags.append(f"Vital sign: abnormal BP ({bp_sys}/{bp_dia} mmHg)")

        # Fever or hypothermia
        if temp > 38.5 or temp < 35.0:
            red_flags.append(f"Vital sign: abnormal temp ({temp}°C)")

        # Tachypnea
        if rr > 24:
            red_flags.append(f"Vital sign: tachypnea (RR = {rr})")

        # Severe pain (8-10/10)
        if pain_scale >= 8:
            red_flags.append(f"Severe pain ({pain_scale}/10)")

        return red_flags

    async def _llm_esi_determination(
        self,
        complaint: str,
        vitals: dict,
        pain_scale: int,
        duration: str,
        history: str,
        entities: dict,
        red_flags: list[str],
        minimum_esi: int
    ) -> dict:
        """
        Use MedGemma 27B via LM Studio to determine ESI score with clinical reasoning.

        Args:
            complaint: Chief complaint
            vitals: Vital signs
            pain_scale: Pain scale
            duration: Symptom duration
            history: Medical history
            entities: Extracted entities
            red_flags: Detected red flags
            minimum_esi: Minimum ESI score (2 if red flags present)

        Returns:
            dict: ESI result with reasoning
        """
        # Build prompt for Claude
        prompt = f"""You are an emergency triage specialist. Determine the Emergency Severity Index (ESI) score for this patient.

PATIENT INFORMATION:
- Chief complaint: {complaint}
- Duration: {duration}
- Vital signs: HR {vitals.get('hr', 'N/A')} bpm, BP {vitals.get('bp_sys', 'N/A')}/{vitals.get('bp_dia', 'N/A')} mmHg, SpO2 {vitals.get('spo2', 'N/A')}%, Temp {vitals.get('temp', 'N/A')}°C, RR {vitals.get('rr', 'N/A')} /min
- Pain scale: {pain_scale}/10
- Medical history: {history}
- Symptoms: {', '.join(entities.get('symptoms', []))}
- Conditions: {', '.join(entities.get('conditions', []))}

RED FLAGS DETECTED ({len(red_flags)}):
{chr(10).join(f"- {flag}" for flag in red_flags) if red_flags else "None"}

ESI CRITERIA:
- ESI-1 Resuscitation: Immediate life-threatening (cardiac arrest, respiratory arrest, severe trauma)
- ESI-2 Emergency: High risk OR severe pain/distress OR altered mental status OR red flags present
- ESI-3 Urgent: Stable but needs multiple resources (labs + imaging + procedures)
- ESI-4 Semi-urgent: Stable, single resource expected
- ESI-5 Non-urgent: No resources expected

CONSTRAINTS:
- Red flags detected = minimum ESI-{minimum_esi}
- Fail-safe UP, never DOWN (when uncertain, escalate urgency)
- Do not diagnose, only assess urgency

Provide your assessment as a JSON object with:
- esi_score (int 1-5, must be <= {minimum_esi} if red flags present)
- esi_label (str, e.g. "ESI-2 Emergency")
- routing (str, recommended department/unit)
- wait_time (str, estimated wait time)
- reasoning (str, clinical reasoning chain explaining the ESI score)
- confidence (float 0.0-1.0, your confidence in this assessment)

Return ONLY valid JSON."""

        # Call LLM API
        response = self.llm_client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        import json
        response_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Enforce minimum ESI constraint (red flags = minimum ESI-2)
        if result["esi_score"] > minimum_esi:
            logger.warning(
                f"Claude suggested ESI-{result['esi_score']}, but red flags require minimum ESI-{minimum_esi}. Adjusting."
            )
            result["esi_score"] = minimum_esi
            result["reasoning"] += f" [Auto-adjusted to ESI-{minimum_esi} due to red flags]"

        # Add red flags to result
        result["red_flags"] = red_flags

        return result

    async def _red_flag_detection(self, params: dict) -> dict:
        """
        Standalone red flag detection skill.

        Args:
            params: Same as esi_scoring params

        Returns:
            dict with red_flags list
        """
        complaint = params.get("complaint", "")
        vitals = params.get("vitals", {})
        pain_scale = params.get("pain_scale", 0)

        # Extract entities for red flag detection
        entities = {"symptoms": [], "conditions": []}
        clinical_bert = get_clinical_bert_service()
        if clinical_bert:
            try:
                clinical_text = f"Chief complaint: {complaint}"
                entities = clinical_bert.extract_entities(clinical_text)
            except Exception:
                pass

        red_flags = self._detect_red_flags(complaint, vitals, entities, pain_scale)

        return {
            "red_flags": red_flags,
            "count": len(red_flags),
            "requires_escalation": len(red_flags) > 0,
            "disclaimer": DISCLAIMER
        }

    async def _patient_routing(self, params: dict) -> dict:
        """
        Determine patient routing based on ESI score and red flags.

        Args:
            params: dict with esi_score and red_flags

        Returns:
            dict with routing recommendation
        """
        esi_score = params.get("esi_score", 5)
        red_flags = params.get("red_flags", [])

        # Routing logic
        if esi_score == 1:
            routing = "Resuscitation bay — IMMEDIATE"
            wait_time = "0 minutes"
        elif esi_score == 2:
            routing = "Emergency department — High priority"
            wait_time = "< 10 minutes"
        elif esi_score == 3:
            routing = "Urgent care area"
            wait_time = "30-60 minutes"
        elif esi_score == 4:
            routing = "Fast track"
            wait_time = "1-2 hours"
        else:  # ESI-5
            routing = "Minor care"
            wait_time = "2-4 hours"

        return {
            "routing": routing,
            "wait_time": wait_time,
            "esi_score": esi_score,
            "requires_immediate_attention": esi_score <= 2,
            "red_flags": red_flags,
            "disclaimer": DISCLAIMER
        }

    async def _emergency_alert(self, params: dict) -> dict:
        """
        Generate emergency alert for ESI 1-2 cases.

        Args:
            params: dict with esi_score, patient info, red_flags

        Returns:
            dict with alert details
        """
        esi_score = params.get("esi_score", 5)
        complaint = params.get("complaint", "")
        red_flags = params.get("red_flags", [])

        if esi_score <= 2:
            alert_level = "CRITICAL" if esi_score == 1 else "URGENT"

            return {
                "alert_level": alert_level,
                "requires_notification": True,
                "notify_roles": ["Attending Physician", "Charge Nurse"] +
                               (["Cardiology"] if any("cardiac" in flag.lower() for flag in red_flags) else []),
                "message": f"{alert_level} ALERT: ESI-{esi_score} patient - {complaint[:100]}",
                "red_flags": red_flags,
                "disclaimer": DISCLAIMER
            }
        else:
            return {
                "alert_level": "NONE",
                "requires_notification": False,
                "message": "No emergency alert required",
                "disclaimer": DISCLAIMER
            }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses about triage assessment.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        # Build triage-specific system prompt
        system_prompt = f"""You are a triage specialist for the MedAssist AI platform.

Your role:
- Assess patient urgency using Emergency Severity Index (ESI 1-5)
- Detect life-threatening red flags
- Provide routing recommendations
- NEVER provide definitive diagnoses
- ALWAYS include disclaimer: "{DISCLAIMER}"

Context:
- Current patient: {context.get('patient_id', 'Unknown')}
- Recent assessments: {context.get('recent_assessments', 'None')}

Respond concisely and professionally."""

        # Stream response from LLM
        stream = self.llm_client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

        # Yield disclaimer at the end
        yield f"\n\n{DISCLAIMER}"


# Global agent instance
_triage_agent = None


def init_triage_agent() -> None:
    """
    Initialize global Triage Agent.
    """
    global _triage_agent
    try:
        _triage_agent = TriageAgent()
        logger.info("Triage Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Triage Agent: {e}")
        _triage_agent = None


def get_triage_agent() -> TriageAgent:
    """
    Get the global Triage Agent instance.

    Returns:
        TriageAgent or None if not initialized
    """
    return _triage_agent
