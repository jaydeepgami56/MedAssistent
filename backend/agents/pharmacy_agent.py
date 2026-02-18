"""
Pharmacy Agent - Drug interaction checking, dosage calculation, and medication reconciliation.

Implements comprehensive drug-drug interaction checking with severity classification
(Critical, Major, Moderate, Minor). Uses RxNorm for drug name resolution and DrugBank
for interaction details. Critical interactions block workflow pending physician override.
"""

import logging
from typing import AsyncIterator, Optional
from backend.llm_client import get_llm_client, LLM_MODEL

from backend.agents.base_agent import BaseAgent
from backend.integrations.rxnorm_client import get_rxnorm_client
from backend.integrations.drugbank_client import get_drugbank_client

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted drug checking — requires pharmacist verification"


class PharmacyAgent(BaseAgent):
    """
    Pharmacy Agent for drug interaction checking and dosage calculation.

    Provides drug-drug interaction detection with severity classification,
    dosage calculation based on patient parameters, contraindication checking,
    and medication reconciliation. Uses RxNorm for drug resolution and DrugBank
    for comprehensive drug information.
    """

    # Severity classification thresholds and criteria
    CRITICAL_KEYWORDS = [
        "life-threatening", "fatal", "death", "respiratory depression",
        "cardiac arrest", "seizure", "coma", "severe bleeding",
        "anaphylaxis", "contraindicated", "avoid combination"
    ]

    MAJOR_KEYWORDS = [
        "significant", "serious", "major", "increased risk",
        "requires monitoring", "dose adjustment", "toxic"
    ]

    def __init__(self):
        """
        Initialize Pharmacy Agent.
        """
        super().__init__(
            agent_id="pharmacy",
            name="Pharmacy Agent",
            skills=[
                "drug_interaction",
                "dosage_calc",
                "contraindication",
                "med_reconciliation"
            ],
            models_used=["MedGemma 27B (LM Studio)", "RxNorm API", "DrugBank API"],
            color="#f59e0b",  # Amber
            icon="[Rx]",  # ASCII-safe icon for Windows console
            status="Active",
            queue=0
        )

        self.llm_client = get_llm_client()

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute pharmacy skill with given parameters.

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

        if skill_name == "drug_interaction":
            return await self._drug_interaction(params)
        elif skill_name == "dosage_calc":
            return await self._dosage_calc(params)
        elif skill_name == "contraindication":
            return await self._contraindication(params)
        elif skill_name == "med_reconciliation":
            return await self._med_reconciliation(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _drug_interaction(self, params: dict) -> dict:
        """
        Check drug-drug interactions with severity classification.

        Args:
            params: dict with keys:
                - drug_names (list[str]): List of drug names to check
                - patient_id (str, optional): Patient identifier
                - patient_conditions (list[str], optional): Patient conditions for context

        Returns:
            dict with keys:
                - interactions (list): List of interaction dicts with drug_a, drug_b,
                  severity, description, evidence_source, blocked
                - alternatives (list): Alternative drug suggestions for blocked interactions
                - summary (str): Human-readable summary
                - total_interactions (int): Total number of interactions found
                - critical_count (int): Number of critical interactions
                - disclaimer (str): Safety disclaimer
        """
        drug_names = params.get("drug_names", [])
        patient_id = params.get("patient_id")
        patient_conditions = params.get("patient_conditions", [])

        if not drug_names or len(drug_names) < 2:
            return {
                "interactions": [],
                "alternatives": [],
                "summary": "Need at least 2 drugs to check for interactions",
                "total_interactions": 0,
                "critical_count": 0,
                "disclaimer": DISCLAIMER,
                "error": "Insufficient drugs provided"
            }

        # Step 1: Resolve drug names to RxCUIs using RxNorm
        rxnorm_client = get_rxnorm_client()
        if not rxnorm_client:
            logger.error("RxNorm client not available")
            return {
                "interactions": [],
                "alternatives": [],
                "summary": "Drug interaction service temporarily unavailable",
                "total_interactions": 0,
                "critical_count": 0,
                "disclaimer": DISCLAIMER,
                "error": "RxNorm client not initialized"
            }

        drug_mapping = {}  # name -> {rxcui, normalized_name}
        for drug_name in drug_names:
            result = await rxnorm_client.resolve_drug_name(drug_name)
            if result.get("found"):
                drug_mapping[drug_name] = {
                    "rxcui": result["rxcui"],
                    "normalized_name": result["name"]
                }
            else:
                logger.warning(f"Could not resolve drug: {drug_name}")

        if len(drug_mapping) < 2:
            return {
                "interactions": [],
                "alternatives": [],
                "summary": f"Could not resolve enough drugs. Resolved: {list(drug_mapping.values())}",
                "total_interactions": 0,
                "critical_count": 0,
                "disclaimer": DISCLAIMER,
                "error": "Drug resolution failed"
            }

        # Step 2: Get interactions from RxNorm
        rxcui_list = [info["rxcui"] for info in drug_mapping.values()]
        rxnorm_interactions = await rxnorm_client.get_interactions(rxcui_list)

        # Step 3: Get additional details from DrugBank
        drugbank_client = get_drugbank_client()
        interactions = []

        for rxnorm_interaction in rxnorm_interactions:
            drug_a_name = rxnorm_interaction["drug_a"]["name"]
            drug_b_name = rxnorm_interaction["drug_b"]["name"]
            description = rxnorm_interaction["description"]
            rxnorm_severity = rxnorm_interaction["severity"]

            # Classify severity with enhanced logic
            severity, blocked = self._classify_severity(description, rxnorm_severity)

            interaction = {
                "drug_a": drug_a_name,
                "drug_b": drug_b_name,
                "severity": severity,
                "description": description,
                "evidence_source": rxnorm_interaction["source"],
                "blocked": blocked
            }

            interactions.append(interaction)

        # Step 4: Get DrugBank interactions for additional context (if available)
        if drugbank_client:
            for drug_name, drug_info in drug_mapping.items():
                drugbank_result = await drugbank_client.search_drug(drug_info["normalized_name"])
                if drugbank_result.get("found"):
                    drugbank_id = drugbank_result["drugbank_id"]
                    drugbank_interactions = await drugbank_client.get_interactions(drugbank_id)

                    # Add DrugBank interactions not already in RxNorm results
                    for db_interaction in drugbank_interactions:
                        # Check if this interaction is already covered
                        existing = any(
                            (i["drug_a"] == drug_info["normalized_name"] and i["drug_b"] == db_interaction["name"]) or
                            (i["drug_b"] == drug_info["normalized_name"] and i["drug_a"] == db_interaction["name"])
                            for i in interactions
                        )

                        if not existing:
                            severity, blocked = self._classify_severity(
                                db_interaction["description"],
                                db_interaction["severity"]
                            )

                            interactions.append({
                                "drug_a": drug_info["normalized_name"],
                                "drug_b": db_interaction["name"],
                                "severity": severity,
                                "description": db_interaction["description"],
                                "evidence_source": "DrugBank",
                                "blocked": blocked
                            })

        # Step 5: Sort by severity (critical first)
        severity_order = {"critical": 0, "major": 1, "moderate": 2, "minor": 3}
        interactions.sort(key=lambda x: severity_order.get(x["severity"], 4))

        # Step 6: Count critical interactions
        critical_count = sum(1 for i in interactions if i["severity"] == "critical")
        blocked_interactions = [i for i in interactions if i["blocked"]]

        # Step 7: Generate alternatives for blocked interactions using Claude
        alternatives = []
        if blocked_interactions:
            alternatives = await self._generate_alternatives(blocked_interactions, patient_conditions)

        # Step 8: Generate summary
        summary = self._generate_interaction_summary(interactions, drug_names)

        # Step 9: Audit logging
        self.log_audit(
            request=f"Drug interaction check: {', '.join(drug_names)}",
            model="RxNorm+DrugBank",
            confidence=1.0 if interactions else 0.5,
            action=f"Found {len(interactions)} interactions, {critical_count} critical"
        )

        return {
            "interactions": interactions,
            "alternatives": alternatives,
            "summary": summary,
            "total_interactions": len(interactions),
            "critical_count": critical_count,
            "disclaimer": DISCLAIMER
        }

    def _classify_severity(self, description: str, api_severity: str) -> tuple[str, bool]:
        """
        Classify interaction severity and determine if workflow should be blocked.

        Args:
            description: Interaction description text
            api_severity: Severity from API (may be "high", "major", etc.)

        Returns:
            tuple: (severity_level, blocked)
                - severity_level: "critical", "major", "moderate", or "minor"
                - blocked: True if critical (requires physician override)
        """
        description_lower = description.lower()
        api_severity_lower = api_severity.lower()

        # Check for critical keywords
        if any(keyword in description_lower for keyword in self.CRITICAL_KEYWORDS):
            return ("critical", True)

        # Check API severity for critical indicators
        if api_severity_lower in ["critical", "contraindicated", "avoid"]:
            return ("critical", True)

        # Check for major keywords
        if any(keyword in description_lower for keyword in self.MAJOR_KEYWORDS):
            return ("major", False)

        # Check API severity for major
        if api_severity_lower in ["high", "major", "serious"]:
            return ("major", False)

        # Check for moderate
        if api_severity_lower in ["moderate", "medium"]:
            return ("moderate", False)

        # Default to minor
        return ("minor", False)

    def _generate_interaction_summary(self, interactions: list[dict], drug_names: list[str]) -> str:
        """
        Generate human-readable summary of interactions.

        Args:
            interactions: List of interaction dicts
            drug_names: Original drug names

        Returns:
            str: Summary text
        """
        if not interactions:
            return f"No interactions found between {', '.join(drug_names)}"

        critical_count = sum(1 for i in interactions if i["severity"] == "critical")
        major_count = sum(1 for i in interactions if i["severity"] == "major")
        moderate_count = sum(1 for i in interactions if i["severity"] == "moderate")
        minor_count = sum(1 for i in interactions if i["severity"] == "minor")

        summary_parts = [
            f"Found {len(interactions)} interaction(s) between {len(drug_names)} drugs:"
        ]

        if critical_count > 0:
            summary_parts.append(f"- {critical_count} CRITICAL (workflow blocked, requires physician override)")
        if major_count > 0:
            summary_parts.append(f"- {major_count} MAJOR (significant risk, monitoring required)")
        if moderate_count > 0:
            summary_parts.append(f"- {moderate_count} MODERATE (dose adjustment may be needed)")
        if minor_count > 0:
            summary_parts.append(f"- {minor_count} MINOR (awareness only)")

        return "\n".join(summary_parts)

    async def _generate_alternatives(self, blocked_interactions: list[dict], patient_conditions: list[str]) -> list[dict]:
        """
        Generate alternative drug suggestions for blocked interactions using MedGemma 27B.

        Args:
            blocked_interactions: List of critical interactions
            patient_conditions: Patient conditions for context

        Returns:
            list of dicts with alternative drug suggestions
        """
        if not blocked_interactions:
            return []

        # Build prompt for Claude
        interactions_text = "\n".join([
            f"- {i['drug_a']} + {i['drug_b']}: {i['description']}"
            for i in blocked_interactions
        ])

        conditions_text = ", ".join(patient_conditions) if patient_conditions else "None specified"

        prompt = f"""You are a clinical pharmacist reviewing critical drug interactions.

BLOCKED INTERACTIONS:
{interactions_text}

PATIENT CONDITIONS: {conditions_text}

For each blocked interaction, suggest alternative medications that would avoid the interaction while treating the same condition. Provide:
1. The drug to replace
2. Alternative medication suggestion
3. Brief rationale

Return as JSON array:
[
  {{
    "drug_to_replace": "drug name",
    "alternative": "alternative drug name",
    "rationale": "brief explanation",
    "therapeutic_class": "drug class"
  }}
]

Focus on commonly used, evidence-based alternatives. Keep rationales concise (1-2 sentences)."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            content = response.choices[0].message.content
            # Strip markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            import json
            alternatives = json.loads(content)

            return alternatives

        except Exception as e:
            logger.error(f"Failed to generate alternatives: {e}")
            return []

    async def _dosage_calc(self, params: dict) -> dict:
        """
        Calculate drug dosage based on patient parameters.

        Args:
            params: dict with keys:
                - drug (str): Drug name
                - weight (float): Patient weight in kg
                - age (int): Patient age in years
                - renal_function (str): "normal", "mild", "moderate", "severe", or eGFR value
                - indication (str, optional): Clinical indication

        Returns:
            dict with keys:
                - drug (str): Drug name
                - dose_range (str): Recommended dose range
                - frequency (str): Dosing frequency
                - route (str): Route of administration
                - adjustments (list): Special considerations
                - disclaimer (str): Safety disclaimer
        """
        drug = params.get("drug", "")
        weight = params.get("weight")
        age = params.get("age")
        renal_function = params.get("renal_function", "normal")
        indication = params.get("indication", "")

        if not drug:
            return {
                "error": "Drug name required",
                "disclaimer": DISCLAIMER
            }

        # Use MedGemma 27B for dosage calculation reasoning
        prompt = f"""You are a clinical pharmacist calculating drug dosages.

DRUG: {drug}
PATIENT WEIGHT: {weight} kg
PATIENT AGE: {age} years
RENAL FUNCTION: {renal_function}
INDICATION: {indication or "Not specified"}

Calculate the appropriate dose range, frequency, and route for this patient. Consider:
1. Weight-based dosing (if applicable)
2. Age-related adjustments (pediatric, geriatric)
3. Renal function adjustments
4. Standard clinical practice

Return as JSON:
{{
  "drug": "{drug}",
  "dose_range": "X-Y mg/kg or absolute dose",
  "frequency": "Every X hours / times per day",
  "route": "oral/IV/IM/etc",
  "adjustments": ["adjustment 1", "adjustment 2"],
  "warnings": ["warning 1", "warning 2"],
  "monitoring": ["parameter 1", "parameter 2"]
}}

Be specific and clinically accurate. Include important warnings and monitoring parameters."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            import json
            dosage_info = json.loads(content)
            dosage_info["disclaimer"] = DISCLAIMER

            # Audit logging
            self.log_audit(
                request=f"Dosage calc: {drug} for {weight}kg, {age}yo, renal: {renal_function}",
                model="MedGemma 27B",
                confidence=0.85,
                action="Dosage calculated"
            )

            return dosage_info

        except Exception as e:
            logger.error(f"Dosage calculation failed: {e}")
            return {
                "drug": drug,
                "error": "Dosage calculation service temporarily unavailable",
                "disclaimer": DISCLAIMER
            }

    async def _contraindication(self, params: dict) -> dict:
        """
        Check drug contraindications for a patient.

        Args:
            params: dict with keys:
                - drug (str): Drug name
                - conditions (list[str]): Patient conditions
                - allergies (list[str], optional): Known allergies

        Returns:
            dict with keys:
                - drug (str): Drug name
                - contraindications (list): List of contraindication dicts with type, condition, severity
                - safe_to_use (bool): Whether drug is safe to use
                - disclaimer (str): Safety disclaimer
        """
        drug = params.get("drug", "")
        conditions = params.get("conditions", [])
        allergies = params.get("allergies", [])

        if not drug:
            return {
                "error": "Drug name required",
                "disclaimer": DISCLAIMER
            }

        # Get DrugBank contraindications
        drugbank_client = get_drugbank_client()
        contraindications = []

        if drugbank_client:
            # First resolve drug name
            rxnorm_client = get_rxnorm_client()
            if rxnorm_client:
                rxnorm_result = await rxnorm_client.resolve_drug_name(drug)
                if rxnorm_result.get("found"):
                    normalized_name = rxnorm_result["name"]

                    # Get DrugBank entry
                    drugbank_result = await drugbank_client.search_drug(normalized_name)
                    if drugbank_result.get("found"):
                        drugbank_id = drugbank_result["drugbank_id"]
                        contraindications = await drugbank_client.get_contraindications(drugbank_id)

        # Check for matching contraindications with patient conditions
        matched_contraindications = []
        for contra in contraindications:
            condition = contra["condition"].lower()
            # Check if any patient condition matches
            if any(patient_condition.lower() in condition or condition in patient_condition.lower()
                   for patient_condition in conditions):
                matched_contraindications.append(contra)

        # Check allergies
        if allergies and any(allergy.lower() in drug.lower() or drug.lower() in allergy.lower()
                            for allergy in allergies):
            matched_contraindications.append({
                "type": "absolute",
                "condition": "Drug allergy",
                "description": f"Patient has documented allergy to {drug}",
                "severity": "critical"
            })

        # Determine if safe to use
        absolute_contraindications = [c for c in matched_contraindications if c.get("type") == "absolute"]
        safe_to_use = len(absolute_contraindications) == 0

        # Audit logging
        self.log_audit(
            request=f"Contraindication check: {drug} for conditions: {conditions}",
            model="DrugBank",
            confidence=1.0 if contraindications else 0.7,
            action=f"Found {len(matched_contraindications)} contraindications, safe: {safe_to_use}"
        )

        return {
            "drug": drug,
            "contraindications": matched_contraindications,
            "all_known_contraindications": contraindications,
            "safe_to_use": safe_to_use,
            "warning": "ABSOLUTE CONTRAINDICATION - DO NOT USE" if absolute_contraindications else None,
            "disclaimer": DISCLAIMER
        }

    async def _med_reconciliation(self, params: dict) -> dict:
        """
        Perform medication reconciliation comparing lists.

        Args:
            params: dict with keys:
                - home_medications (list[str]): Medications patient takes at home
                - hospital_medications (list[str]): Medications ordered in hospital
                - patient_id (str, optional): Patient identifier

        Returns:
            dict with keys:
                - discrepancies (list): List of discrepancy dicts
                - home_only (list): Medications only in home list
                - hospital_only (list): Medications only in hospital list
                - matched (list): Medications in both lists
                - recommendations (str): Reconciliation recommendations
                - disclaimer (str): Safety disclaimer
        """
        home_meds = params.get("home_medications", [])
        hospital_meds = params.get("hospital_medications", [])
        patient_id = params.get("patient_id")

        # Normalize drug names using RxNorm
        rxnorm_client = get_rxnorm_client()
        if not rxnorm_client:
            return {
                "error": "Medication reconciliation service temporarily unavailable",
                "disclaimer": DISCLAIMER
            }

        # Resolve home medications
        home_normalized = {}
        for med in home_meds:
            result = await rxnorm_client.resolve_drug_name(med)
            if result.get("found"):
                home_normalized[result["name"]] = med

        # Resolve hospital medications
        hospital_normalized = {}
        for med in hospital_meds:
            result = await rxnorm_client.resolve_drug_name(med)
            if result.get("found"):
                hospital_normalized[result["name"]] = med

        # Find matches and discrepancies
        home_set = set(home_normalized.keys())
        hospital_set = set(hospital_normalized.keys())

        matched = list(home_set & hospital_set)
        home_only = list(home_set - hospital_set)
        hospital_only = list(hospital_set - home_set)

        # Generate recommendations using MedGemma 27B
        prompt = f"""You are a clinical pharmacist performing medication reconciliation.

HOME MEDICATIONS (not ordered in hospital):
{chr(10).join(['- ' + med for med in home_only]) if home_only else 'None'}

HOSPITAL-ONLY MEDICATIONS (not on home list):
{chr(10).join(['- ' + med for med in hospital_only]) if hospital_only else 'None'}

MATCHED MEDICATIONS:
{chr(10).join(['- ' + med for med in matched]) if matched else 'None'}

Provide reconciliation recommendations:
1. Which home medications should be continued in hospital?
2. Are hospital medications appropriate substitutions?
3. Any potential issues or omissions?

Keep recommendations brief and actionable."""

        try:
            response = self.llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            recommendations = response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to generate reconciliation recommendations: {e}")
            recommendations = "Reconciliation analysis unavailable. Manual review required."

        # Audit logging
        self.log_audit(
            request=f"Med reconciliation: {len(home_meds)} home, {len(hospital_meds)} hospital",
            model="RxNorm+MedGemma 27B",
            confidence=0.9,
            action=f"Found {len(home_only)} home-only, {len(hospital_only)} hospital-only"
        )

        return {
            "discrepancies": {
                "home_only": home_only,
                "hospital_only": hospital_only
            },
            "matched": matched,
            "recommendations": recommendations,
            "total_home": len(home_meds),
            "total_hospital": len(hospital_meds),
            "total_matched": len(matched),
            "disclaimer": DISCLAIMER
        }

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses for pharmacy questions.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        system_prompt = f"""You are a clinical pharmacist AI assistant in the MedAssist AI system.

Your role is to:
- Answer questions about medications, interactions, and dosing
- Provide drug information and clinical pharmacy guidance
- Help with medication reconciliation and safety checks
- Explain pharmacology and therapeutic considerations

IMPORTANT CONSTRAINTS:
- You are a SUPPORT tool, not a replacement for clinical judgment
- Always emphasize the need for pharmacist/physician verification
- Never provide definitive treatment decisions
- Flag potential safety concerns proactively
- Cite evidence sources when possible
- Be clear about uncertainty and limitations

Patient context: {context.get('patient_info', 'No patient context provided')}
Current medications: {context.get('medications', 'None specified')}

Always end responses with: "{DISCLAIMER}"
"""

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

            # Append disclaimer
            yield f"\n\n{DISCLAIMER}"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"I apologize, but I'm having trouble responding right now. Please consult with a pharmacist directly. {DISCLAIMER}"


# Global Pharmacy Agent instance (singleton pattern)
_pharmacy_agent: Optional[PharmacyAgent] = None


async def init_pharmacy_agent() -> PharmacyAgent:
    """
    Initialize the global Pharmacy Agent.

    Returns:
        PharmacyAgent instance
    """
    global _pharmacy_agent

    try:
        _pharmacy_agent = PharmacyAgent()
        logger.info("Pharmacy Agent initialized successfully")
        return _pharmacy_agent
    except Exception as e:
        logger.error(f"Failed to initialize Pharmacy Agent: {e}")
        raise


def get_pharmacy_agent() -> Optional[PharmacyAgent]:
    """
    Get the global Pharmacy Agent instance.

    Returns:
        PharmacyAgent instance or None if not initialized
    """
    return _pharmacy_agent
