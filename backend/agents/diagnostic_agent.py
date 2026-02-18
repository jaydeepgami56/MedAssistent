"""
Diagnostic Agent - Differential diagnosis generation and clinical reasoning.

Implements differential diagnosis pipeline:
1. Accept clinical data (symptoms, vitals, labs, imaging, history)
2. Use Claude API for clinical reasoning (MedGemma 27B fallback planned)
3. Generate ranked differential diagnoses with supporting/contradicting evidence
4. Recommend diagnostic tests based on differential list
5. Identify known symptom-disease patterns
6. Safety checks (confidence < 0.7 flagged for human review)

Provides clinicians with AI-assisted differential diagnosis to support
clinical decision-making. All outputs require clinician verification.
"""

import logging
import json
from typing import AsyncIterator, Optional, Any
from backend.llm_client import get_llm_client, LLM_MODEL

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted — requires clinician verification"

# Common symptom-disease patterns for pattern recognition
KNOWN_PATTERNS = {
    "acute_coronary_syndrome": {
        "symptoms": ["chest pain", "dyspnea", "diaphoresis", "nausea"],
        "vitals": {"hr": ">100", "bp_systolic": ">140 or <90"},
        "red_flags": ["crushing chest pain", "radiation to jaw/arm", "st elevation"]
    },
    "sepsis": {
        "symptoms": ["fever", "chills", "altered mental status", "tachypnea"],
        "vitals": {"temp": ">38.3 or <36", "hr": ">90", "rr": ">20"},
        "red_flags": ["hypotension", "organ dysfunction", "lactate >2"]
    },
    "pulmonary_embolism": {
        "symptoms": ["dyspnea", "chest pain", "tachypnea", "hemoptysis"],
        "vitals": {"hr": ">100", "rr": ">20", "spo2": "<95%"},
        "red_flags": ["sudden onset", "unilateral leg swelling", "recent surgery"]
    },
    "stroke": {
        "symptoms": ["weakness", "facial droop", "speech difficulty", "vision changes"],
        "vitals": {"bp_systolic": ">185"},
        "red_flags": ["sudden onset", "focal neurological deficit", "last known well <4.5h"]
    },
    "diabetic_ketoacidosis": {
        "symptoms": ["polyuria", "polydipsia", "nausea", "vomiting", "abdominal pain"],
        "vitals": {"hr": ">100", "rr": ">20"},
        "red_flags": ["kussmaul breathing", "fruity breath", "glucose >250"]
    },
    "meningitis": {
        "symptoms": ["headache", "fever", "neck stiffness", "photophobia"],
        "vitals": {"temp": ">38.5"},
        "red_flags": ["altered mental status", "petechial rash", "seizures"]
    }
}


class DiagnosticAgent(BaseAgent):
    """
    Diagnostic Agent for differential diagnosis and clinical reasoning.

    Provides differential diagnosis generation, test recommendations,
    and pattern recognition. Uses MedGemma 27B via LM Studio for clinical reasoning.
    """

    def __init__(self):
        """
        Initialize Diagnostic Agent.
        """
        super().__init__(
            agent_id="diagnostic",
            name="Diagnostic Agent",
            skills=[
                "differential_dx",
                "test_recommendation",
                "pattern_recognition",
                "rare_disease"
            ],
            models_used=["MedGemma 27B (LM Studio)"],
            color="#22c55e",  # Green
            icon="🔬",
            status="Active",
            queue=0
        )

        self.llm_client = get_llm_client()
        logger.info("Diagnostic Agent initialized successfully")

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute a specific diagnostic skill.

        Args:
            skill_name: One of: differential_dx, test_recommendation, pattern_recognition, rare_disease
            params: Skill-specific parameters

        Returns:
            dict: Skill execution result

        Raises:
            ValueError: If skill_name is not recognized
        """
        if skill_name not in self.skills:
            raise ValueError(f"Unknown skill: {skill_name}. Available: {self.skills}")

        if skill_name == "differential_dx":
            return await self._differential_dx(params)
        elif skill_name == "test_recommendation":
            return await self._test_recommendation(params)
        elif skill_name == "pattern_recognition":
            return await self._pattern_recognition(params)
        elif skill_name == "rare_disease":
            return await self._rare_disease(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _differential_dx(self, params: dict) -> dict:
        """
        Generate ranked differential diagnoses from clinical data.

        Pipeline:
        1. Extract clinical data (symptoms, vitals, labs, imaging, history)
        2. Use Claude API to generate differential diagnoses
        3. Rank diagnoses by probability
        4. Extract supporting and contradicting evidence for each
        5. Recommend diagnostic tests
        6. Safety check (confidence < 0.7 flagged for human review)

        Args:
            params: dict with keys:
                - symptoms (list[str]): List of patient symptoms
                - vitals (dict): Vital signs {hr, bp_systolic, bp_diastolic, temp, rr, spo2}
                - lab_results (dict, optional): Laboratory results
                - imaging_results (dict, optional): Imaging findings
                - patient_history (dict, optional): Medical history, medications, allergies

        Returns:
            dict with keys:
                - differentials (list): Ranked diagnoses with probability, evidence
                - recommended_tests (list[str]): Suggested diagnostic tests
                - critical_findings (list[str]): Red flags requiring immediate action
                - overall_confidence (float): 0.0-1.0
                - requires_review (bool): True if confidence < 0.7
                - disclaimer (str): Safety disclaimer
        """
        symptoms = params.get("symptoms", [])
        vitals = params.get("vitals", {})
        lab_results = params.get("lab_results", {})
        imaging_results = params.get("imaging_results", {})
        patient_history = params.get("patient_history", {})

        if not symptoms:
            return {
                "error": "symptoms parameter is required",
                "differentials": [],
                "recommended_tests": [],
                "critical_findings": [],
                "overall_confidence": 0.0,
                "requires_review": True,
                "disclaimer": DISCLAIMER
            }

        try:
            # Step 1: Build clinical summary
            clinical_summary = self._build_clinical_summary(
                symptoms, vitals, lab_results, imaging_results, patient_history
            )

            # Step 2: Generate differential diagnosis using MedGemma 27B
            logger.info("Generating differential diagnosis with LLM...")
            diff_dx_prompt = self._build_differential_prompt(clinical_summary)

            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=3000,
                messages=[{"role": "user", "content": diff_dx_prompt}]
            )

            content = response.choices[0].message.content  # type: ignore

            # Step 3: Parse JSON response
            diagnosis_data = self._parse_diagnosis_response(content)

            # Step 4: Calculate overall confidence
            differentials = diagnosis_data.get("differentials", [])
            if differentials:
                # Average the top 3 probabilities
                top_probs = [d["probability"] for d in differentials[:3]]
                overall_confidence = sum(top_probs) / len(top_probs)
            else:
                overall_confidence = 0.0

            # Step 5: Safety check
            requires_review = overall_confidence < 0.7 or len(differentials) == 0

            # Step 6: Extract recommended tests
            recommended_tests = diagnosis_data.get("recommended_tests", [])

            # Step 7: Identify critical findings (red flags)
            critical_findings = diagnosis_data.get("critical_findings", [])

            result = {
                "differentials": differentials,
                "recommended_tests": recommended_tests,
                "critical_findings": critical_findings,
                "overall_confidence": overall_confidence,
                "requires_review": requires_review,
                "clinical_summary": clinical_summary,
                "disclaimer": DISCLAIMER
            }

            # Log audit trail
            self.log_audit(
                request=f"differential_dx: {len(symptoms)} symptoms",
                model="MedGemma 27B",
                confidence=overall_confidence,
                action="flagged_for_review" if requires_review else "processed"
            )

            return result

        except Exception as e:
            logger.error(f"Error in differential_dx: {str(e)}")
            return {
                "error": str(e),
                "differentials": [],
                "recommended_tests": [],
                "critical_findings": [],
                "overall_confidence": 0.0,
                "requires_review": True,
                "disclaimer": DISCLAIMER
            }

    def _build_clinical_summary(
        self,
        symptoms: list[str],
        vitals: dict,
        lab_results: dict,
        imaging_results: dict,
        patient_history: dict
    ) -> str:
        """
        Build structured clinical summary from patient data.

        Args:
            symptoms: List of symptoms
            vitals: Vital signs dict
            lab_results: Laboratory results
            imaging_results: Imaging findings
            patient_history: Medical history

        Returns:
            Formatted clinical summary string
        """
        summary_parts = []

        # Chief complaint / Symptoms
        if symptoms:
            summary_parts.append(f"SYMPTOMS:\n- " + "\n- ".join(symptoms))

        # Vital signs
        if vitals:
            vital_lines = []
            if "hr" in vitals:
                vital_lines.append(f"HR: {vitals['hr']} bpm")
            if "bp_systolic" in vitals and "bp_diastolic" in vitals:
                vital_lines.append(f"BP: {vitals['bp_systolic']}/{vitals['bp_diastolic']} mmHg")
            if "temp" in vitals:
                vital_lines.append(f"Temp: {vitals['temp']}°C")
            if "rr" in vitals:
                vital_lines.append(f"RR: {vitals['rr']} breaths/min")
            if "spo2" in vitals:
                vital_lines.append(f"SpO2: {vitals['spo2']}%")

            if vital_lines:
                summary_parts.append("VITAL SIGNS:\n" + ", ".join(vital_lines))

        # Lab results
        if lab_results:
            lab_lines = [f"{k}: {v}" for k, v in lab_results.items()]
            summary_parts.append("LABORATORY RESULTS:\n- " + "\n- ".join(lab_lines))

        # Imaging
        if imaging_results:
            imaging_lines = [f"{k}: {v}" for k, v in imaging_results.items()]
            summary_parts.append("IMAGING FINDINGS:\n- " + "\n- ".join(imaging_lines))

        # Patient history
        if patient_history:
            history_parts = []
            if "age" in patient_history:
                history_parts.append(f"Age: {patient_history['age']}")
            if "gender" in patient_history:
                history_parts.append(f"Gender: {patient_history['gender']}")
            if "medical_history" in patient_history:
                history_parts.append(f"PMH: {patient_history['medical_history']}")
            if "medications" in patient_history:
                history_parts.append(f"Medications: {patient_history['medications']}")
            if "allergies" in patient_history:
                history_parts.append(f"Allergies: {patient_history['allergies']}")

            if history_parts:
                summary_parts.append("PATIENT HISTORY:\n" + "\n".join(history_parts))

        return "\n\n".join(summary_parts)

    def _build_differential_prompt(self, clinical_summary: str) -> str:
        """
        Build prompt for differential diagnosis generation.

        Args:
            clinical_summary: Formatted clinical summary

        Returns:
            Prompt string for MedGemma 27B
        """
        prompt = f"""You are an expert diagnostician providing differential diagnosis for a clinical case.

CLINICAL PRESENTATION:
{clinical_summary}

Generate a ranked differential diagnosis list. Return your response in JSON format:

{{
  "differentials": [
    {{
      "diagnosis": "Most likely diagnosis name",
      "probability": 0.65,
      "supporting_evidence": [
        "Symptom/finding that supports this diagnosis",
        "Lab/imaging finding that supports this",
        "Historical factor that increases likelihood"
      ],
      "contradicting_evidence": [
        "Finding that argues against this diagnosis (if any)",
        "Missing expected finding"
      ]
    }},
    {{
      "diagnosis": "Second most likely diagnosis",
      "probability": 0.20,
      "supporting_evidence": [...],
      "contradicting_evidence": [...]
    }},
    {{
      "diagnosis": "Third possibility",
      "probability": 0.10,
      "supporting_evidence": [...],
      "contradicting_evidence": [...]
    }}
  ],
  "recommended_tests": [
    "Specific lab test with rationale",
    "Imaging study with indication",
    "Other diagnostic procedure"
  ],
  "critical_findings": [
    "Any red flags requiring immediate intervention",
    "Life-threatening conditions to rule out urgently"
  ]
}}

Requirements:
- Rank diagnoses by probability (probabilities should sum to ~1.0)
- Include 3-5 differential diagnoses
- Provide specific supporting AND contradicting evidence for each
- Base probabilities on clinical likelihood given the presentation
- Recommend tests that will help differentiate between top diagnoses
- Flag any critical/life-threatening conditions in critical_findings
- Be specific with evidence (not just "consistent with symptoms")

IMPORTANT: Return ONLY the JSON object, no other text or explanation."""

        return prompt

    def _parse_diagnosis_response(self, content: str) -> dict[str, Any]:
        """
        Parse diagnosis response from Claude.

        Args:
            content: Raw response text

        Returns:
            Parsed diagnosis dict with differentials, tests, critical_findings
        """
        try:
            # Extract JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            diagnosis_data = json.loads(content)
            return diagnosis_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse diagnosis JSON: {str(e)}")
            # Fallback: return empty structure
            return {
                "differentials": [],
                "recommended_tests": [],
                "critical_findings": []
            }

    async def _test_recommendation(self, params: dict) -> dict:
        """
        Recommend diagnostic tests based on differential diagnosis list.

        Args:
            params: dict with keys:
                - differentials (list): List of differential diagnoses
                - patient_history (dict, optional): Medical history for context

        Returns:
            dict with:
                - recommended_tests (list): Prioritized test recommendations
                - rationale (dict): Test name -> rationale mapping
                - priority (dict): Test name -> priority level (urgent/routine)
                - disclaimer (str)
        """
        differentials = params.get("differentials", [])
        patient_history = params.get("patient_history", {})

        if not differentials:
            return {
                "error": "differentials parameter is required",
                "recommended_tests": [],
                "rationale": {},
                "priority": {},
                "disclaimer": DISCLAIMER
            }

        try:
            # Build prompt for test recommendation
            diff_list = "\n".join([
                f"- {d.get('diagnosis', 'Unknown')} (probability: {d.get('probability', 0.0):.2f})"
                for d in differentials
            ])

            prompt = f"""You are a clinical diagnostician recommending tests to differentiate between diagnoses.

DIFFERENTIAL DIAGNOSES:
{diff_list}

PATIENT CONTEXT:
{json.dumps(patient_history, indent=2) if patient_history else "No additional history provided"}

Recommend diagnostic tests to help narrow the differential. Return JSON:

{{
  "recommended_tests": [
    {{
      "test": "Complete Blood Count (CBC)",
      "rationale": "Evaluate for infection/anemia to distinguish between top diagnoses",
      "priority": "urgent",
      "expected_findings": "Leukocytosis would support infection; anemia might indicate chronic disease"
    }},
    {{
      "test": "Chest X-Ray",
      "rationale": "Rule out pneumonia vs CHF vs PE",
      "priority": "urgent",
      "expected_findings": "Infiltrate = pneumonia; cardiomegaly/edema = CHF; Hampton's hump = PE"
    }}
  ]
}}

Priority levels: "urgent" (STAT/immediate), "routine" (within 24h), "outpatient" (schedule follow-up)

Return ONLY the JSON, no other text."""

            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content  # type: ignore

            # Parse response
            test_data = self._parse_test_response(content)

            # Extract into simplified format
            tests = test_data.get("recommended_tests", [])
            recommended_tests = [t["test"] for t in tests]
            rationale = {t["test"]: t["rationale"] for t in tests}
            priority = {t["test"]: t["priority"] for t in tests}

            # Log audit
            self.log_audit(
                request=f"test_recommendation: {len(differentials)} differentials",
                model="MedGemma 27B",
                confidence=0.85,
                action=f"recommended_{len(recommended_tests)}_tests"
            )

            return {
                "recommended_tests": recommended_tests,
                "rationale": rationale,
                "priority": priority,
                "detailed_tests": tests,  # Full test objects
                "disclaimer": DISCLAIMER
            }

        except Exception as e:
            logger.error(f"Error in test_recommendation: {str(e)}")
            return {
                "error": str(e),
                "recommended_tests": [],
                "rationale": {},
                "priority": {},
                "disclaimer": DISCLAIMER
            }

    def _parse_test_response(self, content: str) -> dict[str, Any]:
        """Parse test recommendation response."""
        try:
            # Extract JSON from markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            test_data = json.loads(content)
            return test_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse test JSON: {str(e)}")
            return {"recommended_tests": []}

    async def _pattern_recognition(self, params: dict) -> dict:
        """
        Identify known symptom-disease patterns in clinical presentation.

        Checks against KNOWN_PATTERNS for rapid recognition of common
        critical presentations (ACS, sepsis, PE, stroke, DKA, meningitis).

        Args:
            params: dict with keys:
                - symptoms (list[str]): Patient symptoms
                - vitals (dict): Vital signs

        Returns:
            dict with:
                - matched_patterns (list): List of matched pattern names
                - pattern_details (dict): Pattern name -> match details
                - alerts (list[str]): Critical alerts for matched patterns
                - disclaimer (str)
        """
        symptoms = params.get("symptoms", [])
        vitals = params.get("vitals", {})

        if not symptoms:
            return {
                "matched_patterns": [],
                "pattern_details": {},
                "alerts": [],
                "disclaimer": DISCLAIMER
            }

        # Normalize symptoms to lowercase for matching
        symptoms_lower = [s.lower() for s in symptoms]

        matched_patterns = []
        pattern_details = {}
        alerts = []

        # Check each known pattern
        for pattern_name, pattern_data in KNOWN_PATTERNS.items():
            pattern_symptoms = [s.lower() for s in pattern_data["symptoms"]]

            # Check symptom overlap
            symptom_matches = [s for s in pattern_symptoms if any(ps in symptoms_lower for ps in [s])]
            symptom_match_count = len(symptom_matches)

            # Check vital signs (simplified matching)
            vital_matches = []
            if vitals:
                for vital_key, vital_criteria in pattern_data.get("vitals", {}).items():
                    if vital_key in vitals:
                        # This is simplified - could be enhanced with range parsing
                        vital_matches.append(vital_key)

            # Pattern is matched if >= 50% symptoms match OR critical vitals match
            match_threshold = len(pattern_symptoms) * 0.5
            if symptom_match_count >= match_threshold or len(vital_matches) >= 2:
                matched_patterns.append(pattern_name)

                # Calculate match confidence
                confidence = symptom_match_count / len(pattern_symptoms)

                pattern_details[pattern_name] = {
                    "matched_symptoms": symptom_matches,
                    "matched_vitals": vital_matches,
                    "red_flags": pattern_data.get("red_flags", []),
                    "confidence": round(confidence, 2)
                }

                # Generate alert for critical patterns
                readable_name = pattern_name.replace("_", " ").title()
                alerts.append(
                    f"ALERT: Pattern consistent with {readable_name}. "
                    f"Consider: {', '.join(pattern_data.get('red_flags', [])[:2])}"
                )

        # Log audit
        self.log_audit(
            request=f"pattern_recognition: {len(symptoms)} symptoms",
            model="Rule-based pattern matching",
            confidence=0.90,
            action=f"matched_{len(matched_patterns)}_patterns"
        )

        return {
            "matched_patterns": matched_patterns,
            "pattern_details": pattern_details,
            "alerts": alerts,
            "disclaimer": DISCLAIMER
        }

    async def _rare_disease(self, params: dict) -> dict:
        """
        Search for rare disease matches (placeholder for future implementation).

        Future versions will integrate with GARD (Genetic and Rare Diseases),
        Orphanet, or similar rare disease databases.

        Args:
            params: dict with clinical data

        Returns:
            dict with message and disclaimer
        """
        return {
            "message": "Rare disease search is not yet implemented. Future versions will integrate with GARD/Orphanet databases.",
            "rare_diseases": [],
            "disclaimer": DISCLAIMER
        }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses for diagnostic questions.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        system_prompt = """You are the Diagnostic Agent in MedAssist AI, a clinical decision support system.

Your role:
- Generate differential diagnoses from clinical presentations
- Provide clinical reasoning for diagnostic possibilities
- Recommend diagnostic tests to narrow differentials
- Identify critical symptom patterns requiring urgent intervention
- Assist with complex diagnostic cases

Guidelines:
- Present differentials with supporting AND contradicting evidence
- Rank diagnoses by clinical probability
- Always consider life-threatening conditions first (VINDICATE-P approach)
- Recommend tests that will meaningfully change management
- Flag red flags requiring immediate intervention
- Be explicit about diagnostic uncertainty
- Include disclaimer: "AI-assisted — requires clinician verification"

Available skills:
- differential_dx: Generate ranked differential diagnosis list
- test_recommendation: Suggest diagnostic tests based on differentials
- pattern_recognition: Identify known critical symptom patterns
- rare_disease: Search rare disease databases (coming soon)

You assist with diagnosis — you never make final diagnostic determinations.
All diagnoses require clinician verification and clinical judgment."""

        try:
            # Stream response from LLM
            stream = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            # Add disclaimer at the end
            yield f"\n\n---\n{DISCLAIMER}"

        except Exception as e:
            logger.error(f"Error in diagnostic chat: {str(e)}")
            yield f"Error: {str(e)}\n\n{DISCLAIMER}"


# Global Diagnostic Agent instance (singleton pattern)
_diagnostic_agent: Optional[DiagnosticAgent] = None


def init_diagnostic_agent() -> DiagnosticAgent:
    """
    Initialize the global Diagnostic Agent.

    Returns:
        DiagnosticAgent instance
    """
    global _diagnostic_agent
    _diagnostic_agent = DiagnosticAgent()
    return _diagnostic_agent


def get_diagnostic_agent() -> Optional[DiagnosticAgent]:
    """
    Get the global Diagnostic Agent instance.

    Returns:
        DiagnosticAgent instance or None if not initialized
    """
    return _diagnostic_agent
