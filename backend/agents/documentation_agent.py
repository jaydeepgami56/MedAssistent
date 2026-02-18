"""
Documentation Agent - Clinical note generation with SOAP format and ICD-10 coding.

Implements automated clinical documentation generation including SOAP notes,
discharge summaries, and ICD-10 code suggestions. All notes are auto-generated
as drafts requiring clinician review and approval before finalization.
"""

import logging
import json
from typing import AsyncIterator, Optional
from backend.llm_client import get_llm_client, LLM_MODEL

from backend.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "Auto-generated — review and edit before finalizing"


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent for clinical note generation and medical coding.

    Provides automated SOAP note generation, discharge summaries, ICD-10 coding,
    and referral letters. Uses MedGemma 27B via LM Studio for clinical reasoning and structured
    documentation generation. All outputs are drafts requiring clinician approval.
    """

    def __init__(self):
        """
        Initialize Documentation Agent.
        """
        super().__init__(
            agent_id="docs",
            name="Documentation Agent",
            skills=[
                "soap_notes",
                "discharge_summary",
                "icd10_coding",
                "referral_letter"
            ],
            models_used=["MedGemma 27B (LM Studio)"],
            color="#06b6d4",  # Cyan
            icon="📋",
            status="Active",
            queue=0
        )

        self.llm_client = get_llm_client()

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute documentation skill with given parameters.

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

        if skill_name == "soap_notes":
            return await self._soap_notes(params)
        elif skill_name == "discharge_summary":
            return await self._discharge_summary(params)
        elif skill_name == "icd10_coding":
            return await self._icd10_coding(params)
        elif skill_name == "referral_letter":
            return await self._referral_letter(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _soap_notes(self, params: dict) -> dict:
        """
        Generate SOAP note from encounter data.

        Args:
            params: dict with keys:
                - patient_id (str): Patient identifier
                - encounter_data (dict): Encounter information with keys:
                    - transcript (str, optional): Patient interview transcript
                    - triage_output (dict, optional): Triage agent results
                    - radiology_output (dict, optional): Radiology agent results
                    - pharmacy_output (dict, optional): Pharmacy agent results
                    - monitoring_output (dict, optional): Monitoring agent results
                    - chief_complaint (str, optional): Chief complaint
                    - physical_exam (str, optional): Physical exam findings

        Returns:
            dict with keys:
                - soap_sections (dict): Dictionary with S, O, A, P sections
                - icd10_codes (list): Auto-suggested ICD-10 codes from Assessment
                - draft_status (str): Always "pending_review"
                - confidence (float): Confidence in documentation quality
                - disclaimer (str): Safety disclaimer
        """
        patient_id = params.get("patient_id", "unknown")
        encounter_data = params.get("encounter_data", {})

        # Extract data from encounter
        transcript = encounter_data.get("transcript", "")
        chief_complaint = encounter_data.get("chief_complaint", "")
        physical_exam = encounter_data.get("physical_exam", "")
        triage_output = encounter_data.get("triage_output", {})
        radiology_output = encounter_data.get("radiology_output", {})
        pharmacy_output = encounter_data.get("pharmacy_output", {})
        monitoring_output = encounter_data.get("monitoring_output", {})

        # Build comprehensive prompt for MedGemma 27B
        prompt = self._build_soap_prompt(
            chief_complaint=chief_complaint,
            transcript=transcript,
            physical_exam=physical_exam,
            triage_output=triage_output,
            radiology_output=radiology_output,
            pharmacy_output=pharmacy_output,
            monitoring_output=monitoring_output
        )

        try:
            # Generate SOAP note using LLM
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content

            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            soap_data = json.loads(content)

            # Extract SOAP sections
            soap_sections = {
                "subjective": soap_data.get("subjective", ""),
                "objective": soap_data.get("objective", ""),
                "assessment": soap_data.get("assessment", ""),
                "plan": soap_data.get("plan", "")
            }

            # Extract ICD-10 codes
            icd10_codes = soap_data.get("icd10_codes", [])

            # Calculate confidence based on completeness
            confidence = self._calculate_soap_confidence(
                soap_sections=soap_sections,
                encounter_data=encounter_data
            )

            result = {
                "soap_sections": soap_sections,
                "icd10_codes": icd10_codes,
                "draft_status": "pending_review",
                "confidence": confidence,
                "patient_id": patient_id,
                "disclaimer": DISCLAIMER
            }

            # Audit logging
            self.log_audit(
                request=f"SOAP note generation for patient {patient_id}",
                model="MedGemma 27B",
                confidence=confidence,
                action="SOAP note draft created"
            )

            return result

        except Exception as e:
            logger.error(f"SOAP note generation failed: {e}")
            return {
                "soap_sections": {
                    "subjective": "",
                    "objective": "",
                    "assessment": "",
                    "plan": ""
                },
                "icd10_codes": [],
                "draft_status": "error",
                "confidence": 0.0,
                "error": f"SOAP note generation failed: {str(e)}",
                "disclaimer": DISCLAIMER
            }

    def _build_soap_prompt(
        self,
        chief_complaint: str,
        transcript: str,
        physical_exam: str,
        triage_output: dict,
        radiology_output: dict,
        pharmacy_output: dict,
        monitoring_output: dict
    ) -> str:
        """
        Build comprehensive prompt for SOAP note generation.

        Args:
            chief_complaint: Patient's chief complaint
            transcript: Patient interview transcript
            physical_exam: Physical examination findings
            triage_output: Triage agent results
            radiology_output: Radiology agent results
            pharmacy_output: Pharmacy agent results
            monitoring_output: Monitoring agent results

        Returns:
            str: Formatted prompt for MedGemma 27B
        """
        prompt_parts = [
            "You are a clinical documentation specialist generating a SOAP note from encounter data.",
            "",
            "Generate a comprehensive SOAP (Subjective, Objective, Assessment, Plan) note with the following sections:",
            ""
        ]

        # Add available data
        if chief_complaint:
            prompt_parts.append(f"CHIEF COMPLAINT: {chief_complaint}")
            prompt_parts.append("")

        if transcript:
            prompt_parts.append(f"PATIENT INTERVIEW TRANSCRIPT:\n{transcript}")
            prompt_parts.append("")

        if physical_exam:
            prompt_parts.append(f"PHYSICAL EXAM FINDINGS:\n{physical_exam}")
            prompt_parts.append("")

        if triage_output:
            prompt_parts.append("TRIAGE DATA:")
            prompt_parts.append(f"- ESI Level: {triage_output.get('esi_level', 'N/A')}")
            prompt_parts.append(f"- Vital Signs: {triage_output.get('vital_signs', {})}")
            if triage_output.get('red_flags'):
                prompt_parts.append(f"- Red Flags: {', '.join(triage_output['red_flags'])}")
            prompt_parts.append("")

        if monitoring_output:
            prompt_parts.append("VITAL SIGNS MONITORING:")
            vitals = monitoring_output.get('vitals', {})
            prompt_parts.append(f"- HR: {vitals.get('hr', 'N/A')} bpm")
            prompt_parts.append(f"- BP: {vitals.get('bp_sys', 'N/A')}/{vitals.get('bp_dia', 'N/A')} mmHg")
            prompt_parts.append(f"- SpO2: {vitals.get('spo2', 'N/A')}%")
            prompt_parts.append(f"- Temp: {vitals.get('temp', 'N/A')}°C")
            prompt_parts.append(f"- RR: {vitals.get('rr', 'N/A')}/min")
            if monitoring_output.get('mews_total') is not None:
                prompt_parts.append(f"- MEWS Score: {monitoring_output['mews_total']}")
            prompt_parts.append("")

        if radiology_output:
            prompt_parts.append("IMAGING RESULTS:")
            prompt_parts.append(f"- Study: {radiology_output.get('study_type', 'N/A')}")
            prompt_parts.append(f"- Findings: {radiology_output.get('findings', 'N/A')}")
            if radiology_output.get('primary_diagnosis'):
                prompt_parts.append(f"- Impression: {radiology_output['primary_diagnosis']}")
            prompt_parts.append("")

        if pharmacy_output:
            prompt_parts.append("PHARMACY REVIEW:")
            if pharmacy_output.get('interactions'):
                prompt_parts.append(f"- Drug Interactions: {len(pharmacy_output['interactions'])} found")
            if pharmacy_output.get('contraindications'):
                prompt_parts.append(f"- Contraindications: {pharmacy_output.get('contraindications', [])}")
            prompt_parts.append("")

        # Add instructions for SOAP format
        prompt_parts.extend([
            "Generate a SOAP note in JSON format:",
            "{",
            '  "subjective": "Patient presentation in their own words, HPI, relevant history",',
            '  "objective": "Vital signs, physical exam findings, labs, imaging results",',
            '  "assessment": "Clinical assessment, differential diagnoses, working diagnosis",',
            '  "plan": "Treatment plan, medications, follow-up, patient education",',
            '  "icd10_codes": [',
            '    {',
            '      "code": "ICD-10 code",',
            '      "description": "Code description",',
            '      "confidence": 0.0-1.0',
            '    }',
            '  ]',
            '}',
            "",
            "IMPORTANT:",
            "- Subjective (S): Use patient's own words, symptoms, timeline, relevant history",
            "- Objective (O): Include all vitals, exam findings, lab/imaging results",
            "- Assessment (A): Provide clinical reasoning, differentials, working diagnosis",
            "- Plan (P): Specific treatments, medications, follow-up instructions, patient education",
            "- ICD-10 codes: Suggest 1-5 codes from Assessment with confidence scores",
            "- Be thorough but concise",
            "- Use clinical terminology appropriately",
            "- Include all relevant data from the encounter"
        ])

        return "\n".join(prompt_parts)

    def _calculate_soap_confidence(self, soap_sections: dict, encounter_data: dict) -> float:
        """
        Calculate confidence score based on SOAP note completeness.

        Args:
            soap_sections: Generated SOAP sections
            encounter_data: Original encounter data

        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.0

        # Check if all sections are populated (0.4 points)
        sections_populated = sum(
            1 for section in soap_sections.values()
            if section and len(section.strip()) > 20
        )
        confidence += (sections_populated / 4) * 0.4

        # Check if we had good source data (0.3 points)
        data_sources = 0
        if encounter_data.get("transcript"):
            data_sources += 1
        if encounter_data.get("triage_output"):
            data_sources += 1
        if encounter_data.get("physical_exam"):
            data_sources += 1
        if encounter_data.get("radiology_output") or encounter_data.get("monitoring_output"):
            data_sources += 1

        confidence += (min(data_sources, 4) / 4) * 0.3

        # Base quality score (0.3 points)
        confidence += 0.3

        return round(confidence, 2)

    async def _discharge_summary(self, params: dict) -> dict:
        """
        Generate discharge summary from encounter history.

        Args:
            params: dict with keys:
                - patient_id (str): Patient identifier
                - admission_date (str): Admission date
                - discharge_date (str): Discharge date
                - hospital_course (str): Description of hospital stay
                - encounter_history (list[dict]): List of encounter notes
                - discharge_medications (list[str]): Medications at discharge
                - follow_up_plan (str): Follow-up instructions

        Returns:
            dict with keys:
                - summary (str): Formatted discharge summary
                - sections (dict): Individual sections of the summary
                - draft_status (str): Always "pending_review"
                - disclaimer (str): Safety disclaimer
        """
        patient_id = params.get("patient_id", "unknown")
        admission_date = params.get("admission_date", "")
        discharge_date = params.get("discharge_date", "")
        hospital_course = params.get("hospital_course", "")
        encounter_history = params.get("encounter_history", [])
        discharge_medications = params.get("discharge_medications", [])
        follow_up_plan = params.get("follow_up_plan", "")

        # Build prompt for discharge summary
        prompt = f"""You are a clinical documentation specialist generating a discharge summary.

PATIENT ID: {patient_id}
ADMISSION DATE: {admission_date}
DISCHARGE DATE: {discharge_date}

HOSPITAL COURSE:
{hospital_course}

ENCOUNTER HISTORY:
{json.dumps(encounter_history, indent=2) if encounter_history else "No encounter history provided"}

DISCHARGE MEDICATIONS:
{chr(10).join(['- ' + med for med in discharge_medications]) if discharge_medications else "None specified"}

FOLLOW-UP PLAN:
{follow_up_plan}

Generate a comprehensive discharge summary in JSON format:
{{
  "admission_diagnosis": "Primary diagnosis on admission",
  "discharge_diagnosis": "Final diagnosis at discharge",
  "hospital_course": "Narrative summary of hospital stay",
  "procedures": ["procedure 1", "procedure 2"],
  "complications": "Any complications or issues",
  "discharge_condition": "Patient condition at discharge",
  "discharge_medications": ["med 1", "med 2"],
  "follow_up": "Follow-up instructions and appointments",
  "patient_education": "Patient education provided"
}}

Be thorough, professional, and clinically accurate."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=3072,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            sections = json.loads(content)

            # Format as readable summary
            summary_parts = [
                "DISCHARGE SUMMARY",
                "=" * 60,
                f"Patient ID: {patient_id}",
                f"Admission Date: {admission_date}",
                f"Discharge Date: {discharge_date}",
                "",
                f"ADMISSION DIAGNOSIS: {sections.get('admission_diagnosis', 'N/A')}",
                "",
                f"DISCHARGE DIAGNOSIS: {sections.get('discharge_diagnosis', 'N/A')}",
                "",
                "HOSPITAL COURSE:",
                sections.get('hospital_course', 'N/A'),
                "",
                "PROCEDURES PERFORMED:",
                "\n".join([f"- {proc}" for proc in sections.get('procedures', [])]) or "None",
                "",
                f"COMPLICATIONS: {sections.get('complications', 'None')}",
                "",
                f"DISCHARGE CONDITION: {sections.get('discharge_condition', 'N/A')}",
                "",
                "DISCHARGE MEDICATIONS:",
                "\n".join([f"- {med}" for med in sections.get('discharge_medications', [])]) or "None",
                "",
                "FOLLOW-UP:",
                sections.get('follow_up', 'N/A'),
                "",
                "PATIENT EDUCATION:",
                sections.get('patient_education', 'N/A')
            ]

            summary = "\n".join(summary_parts)

            result = {
                "summary": summary,
                "sections": sections,
                "draft_status": "pending_review",
                "patient_id": patient_id,
                "disclaimer": DISCLAIMER
            }

            # Audit logging
            self.log_audit(
                request=f"Discharge summary for patient {patient_id}",
                model="MedGemma 27B",
                confidence=0.85,
                action="Discharge summary draft created"
            )

            return result

        except Exception as e:
            logger.error(f"Discharge summary generation failed: {e}")
            return {
                "summary": "",
                "sections": {},
                "draft_status": "error",
                "error": f"Discharge summary generation failed: {str(e)}",
                "disclaimer": DISCLAIMER
            }

    async def _icd10_coding(self, params: dict) -> dict:
        """
        Generate ICD-10 code suggestions from clinical text.

        Args:
            params: dict with keys:
                - clinical_text (str): Clinical notes or assessment text
                - diagnosis_list (list[str], optional): List of diagnoses
                - top_k (int, optional): Number of codes to return (default: 5)

        Returns:
            dict with keys:
                - icd10_codes (list): List of code dicts with code, description, confidence
                - primary_code (dict): Suggested primary diagnosis code
                - draft_status (str): Always "pending_review"
                - disclaimer (str): Safety disclaimer
        """
        clinical_text = params.get("clinical_text", "")
        diagnosis_list = params.get("diagnosis_list", [])
        top_k = params.get("top_k", 5)

        if not clinical_text and not diagnosis_list:
            return {
                "icd10_codes": [],
                "primary_code": None,
                "draft_status": "error",
                "error": "Either clinical_text or diagnosis_list required",
                "disclaimer": DISCLAIMER
            }

        # Build prompt for ICD-10 coding
        prompt_parts = [
            "You are a medical coding specialist assigning ICD-10 codes.",
            ""
        ]

        if clinical_text:
            prompt_parts.append(f"CLINICAL NOTES:\n{clinical_text}")
            prompt_parts.append("")

        if diagnosis_list:
            prompt_parts.append("DIAGNOSES:")
            prompt_parts.extend([f"- {dx}" for dx in diagnosis_list])
            prompt_parts.append("")

        prompt_parts.extend([
            f"Generate the top {top_k} most appropriate ICD-10 codes in JSON format:",
            "[",
            "  {",
            '    "code": "ICD-10 code (e.g., J18.9)",',
            '    "description": "Full description",',
            '    "confidence": 0.0-1.0,',
            '    "is_primary": true/false',
            "  }",
            "]",
            "",
            "IMPORTANT:",
            "- Use current ICD-10-CM codes (2024/2025)",
            "- Assign confidence based on specificity and documentation support",
            "- Mark the most likely primary diagnosis with is_primary: true",
            "- Include both specific and differential codes",
            "- Order by confidence (highest first)"
        ])

        prompt = "\n".join(prompt_parts)

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            icd10_codes = json.loads(content)

            # Find primary code
            primary_code = next(
                (code for code in icd10_codes if code.get("is_primary", False)),
                icd10_codes[0] if icd10_codes else None
            )

            result = {
                "icd10_codes": icd10_codes,
                "primary_code": primary_code,
                "draft_status": "pending_review",
                "disclaimer": DISCLAIMER
            }

            # Audit logging
            self.log_audit(
                request="ICD-10 coding from clinical text",
                model="MedGemma 27B",
                confidence=primary_code.get("confidence", 0.0) if primary_code else 0.0,
                action=f"{len(icd10_codes)} codes suggested"
            )

            return result

        except Exception as e:
            logger.error(f"ICD-10 coding failed: {e}")
            return {
                "icd10_codes": [],
                "primary_code": None,
                "draft_status": "error",
                "error": f"ICD-10 coding failed: {str(e)}",
                "disclaimer": DISCLAIMER
            }

    async def _referral_letter(self, params: dict) -> dict:
        """
        Generate referral letter to specialist.

        Args:
            params: dict with keys:
                - patient_id (str): Patient identifier
                - patient_name (str): Patient name
                - referring_provider (str): Referring provider name
                - specialist_type (str): Type of specialist (e.g., "Cardiology", "Neurology")
                - reason_for_referral (str): Clinical reason for referral
                - relevant_history (str): Relevant medical history
                - current_medications (list[str], optional): Current medications
                - attachments (list[str], optional): List of attached documents

        Returns:
            dict with keys:
                - letter (str): Formatted referral letter
                - draft_status (str): Always "pending_review"
                - disclaimer (str): Safety disclaimer
        """
        patient_id = params.get("patient_id", "unknown")
        patient_name = params.get("patient_name", "")
        referring_provider = params.get("referring_provider", "")
        specialist_type = params.get("specialist_type", "")
        reason_for_referral = params.get("reason_for_referral", "")
        relevant_history = params.get("relevant_history", "")
        current_medications = params.get("current_medications", [])
        attachments = params.get("attachments", [])

        # Build prompt for referral letter
        prompt = f"""You are a clinical documentation specialist generating a referral letter.

Generate a professional referral letter with the following information:

TO: {specialist_type} Specialist
FROM: {referring_provider}
PATIENT: {patient_name} (ID: {patient_id})

REASON FOR REFERRAL:
{reason_for_referral}

RELEVANT CLINICAL HISTORY:
{relevant_history}

CURRENT MEDICATIONS:
{chr(10).join(['- ' + med for med in current_medications]) if current_medications else "None"}

ATTACHMENTS:
{chr(10).join(['- ' + att for att in attachments]) if attachments else "None"}

Generate a professional, concise referral letter that:
1. Clearly states the reason for referral
2. Provides relevant clinical context
3. Includes pertinent history and current treatment
4. Requests specific consultation or intervention
5. Is formatted professionally

Return the letter as plain text, properly formatted."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            letter = response.choices[0].message.content

            result = {
                "letter": letter,
                "draft_status": "pending_review",
                "patient_id": patient_id,
                "specialist_type": specialist_type,
                "disclaimer": DISCLAIMER
            }

            # Audit logging
            self.log_audit(
                request=f"Referral letter to {specialist_type} for patient {patient_id}",
                model="MedGemma 27B",
                confidence=0.90,
                action="Referral letter draft created"
            )

            return result

        except Exception as e:
            logger.error(f"Referral letter generation failed: {e}")
            return {
                "letter": "",
                "draft_status": "error",
                "error": f"Referral letter generation failed: {str(e)}",
                "disclaimer": DISCLAIMER
            }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses about clinical documentation.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        system_prompt = f"""You are a clinical documentation specialist for the MedAssist AI platform.

Your role:
- Assist with clinical note generation (SOAP, discharge summaries, referrals)
- Help with ICD-10 coding and medical terminology
- Provide documentation best practices and templates
- Answer questions about clinical documentation standards
- NEVER provide definitive diagnoses
- ALWAYS include disclaimer: "{DISCLAIMER}"

Context:
- Current patient: {context.get('patient_id', 'Unknown')}
- Documentation type: {context.get('doc_type', 'General')}

Respond concisely and professionally. All generated documentation is draft-only and requires clinician review."""

        try:
            # Stream response from LLM
            stream = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2048,
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

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"I apologize, but I'm having trouble responding right now. {DISCLAIMER}"


# Global agent instance
_documentation_agent: Optional[DocumentationAgent] = None


def init_documentation_agent() -> DocumentationAgent:
    """
    Initialize global Documentation Agent.

    Returns:
        DocumentationAgent instance
    """
    global _documentation_agent

    try:
        _documentation_agent = DocumentationAgent()
        logger.info("Documentation Agent initialized successfully")
        return _documentation_agent
    except Exception as e:
        logger.error(f"Failed to initialize Documentation Agent: {e}")
        raise


def get_documentation_agent() -> Optional[DocumentationAgent]:
    """
    Get the global Documentation Agent instance.

    Returns:
        DocumentationAgent or None if not initialized
    """
    return _documentation_agent
