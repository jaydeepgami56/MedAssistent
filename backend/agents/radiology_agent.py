"""
Radiology Agent - Medical image analysis with KNN evidence search and report generation.

Implements medical image analysis pipeline:
1. MedImageInsight classification (zero-shot)
2. Embedding generation and storage in Qdrant
3. KNN evidence search for similar historical cases
4. MedGemma report generation with findings and evidence
5. Safety checks (confidence < 0.7 flagged for human review)

Supports multiple imaging modalities: Chest X-Ray, Brain MRI, Chest CT,
Musculoskeletal X-Ray, and Dermatology.
"""

import logging
from typing import AsyncIterator, Union
from io import BytesIO
from anthropic import Anthropic
from PIL import Image

from backend.agents.base_agent import BaseAgent
from backend.models.medimageinsight import get_medimageinsight_service
from backend.models.medgemma import get_medgemma_service
from backend.integrations.qdrant_client import get_qdrant_service

logger = logging.getLogger(__name__)

# DISCLAIMER - MUST be included in ALL outputs
DISCLAIMER = "AI-assisted analysis — requires radiologist review"

# Collection name for medical image embeddings in Qdrant
MEDICAL_IMAGES_COLLECTION = "medical_images"


class RadiologyAgent(BaseAgent):
    """
    Radiology Agent for medical image analysis.

    Provides image classification, KNN evidence search, and report generation
    for various imaging modalities. Uses MedImageInsight for classification/embeddings,
    Qdrant for KNN search, and MedGemma for report narrative generation.
    """

    def __init__(self, anthropic_api_key: str):
        """
        Initialize Radiology Agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude reasoning
        """
        super().__init__(
            agent_id="radiology",
            name="Radiology Agent",
            skills=[
                "xray_analysis",
                "mri_interpretation",
                "ct_review",
                "report_gen",
                "evidence_search"
            ],
            models_used=["MedImageInsight", "MedGemma 4B", "Qdrant"],
            color="#00b4d8",  # Cyan-blue
            icon="🩻",  # X-ray emoji
            status="Active",
            queue=0
        )

        self.anthropic_client = Anthropic(api_key=anthropic_api_key)

    async def execute_skill(self, skill_name: str, params: dict) -> dict:
        """
        Execute radiology skill with given parameters.

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

        if skill_name == "xray_analysis":
            return await self._xray_analysis(params)
        elif skill_name == "mri_interpretation":
            return await self._mri_interpretation(params)
        elif skill_name == "ct_review":
            return await self._ct_review(params)
        elif skill_name == "report_gen":
            return await self._report_gen(params)
        elif skill_name == "evidence_search":
            return await self._evidence_search(params)
        else:
            raise ValueError(f"Skill not implemented: {skill_name}")

    async def _xray_analysis(self, params: dict) -> dict:
        """
        Analyze chest X-ray image with full pipeline.

        Pipeline:
        1. Load and validate image
        2. MedImageInsight classification with CHEST_XRAY_LABELS
        3. Generate embedding
        4. Store embedding in Qdrant with metadata
        5. Search for similar cases (KNN)
        6. Generate report narrative with MedGemma
        7. Safety check (flag if confidence < 0.7)

        Args:
            params: dict with keys:
                - image (PIL.Image or bytes): Medical image
                - patient_info (dict): name, age, gender, medical_history
                - clinical_indication (str): Reason for imaging (optional)
                - image_id (str): Unique identifier for this image (optional)

        Returns:
            dict with keys:
                - findings (list): [{text, confidence, severity}]
                - similar_cases (list): [{id, similarity_score, metadata}]
                - recommendation (str): Clinical recommendation
                - overall_confidence (float): 0.0-1.0
                - requires_review (bool): True if confidence < 0.7
                - report_narrative (str): Structured radiology report
                - disclaimer (str): Safety disclaimer
        """
        # Extract parameters
        image = params.get("image")
        patient_info = params.get("patient_info", {})
        clinical_indication = params.get("clinical_indication", "Routine chest X-ray")
        image_id = params.get("image_id", None)

        if image is None:
            raise ValueError("image parameter is required")

        # Convert bytes to PIL Image if needed
        if isinstance(image, bytes):
            image = Image.open(BytesIO(image))

        # Get MedImageInsight service
        medimageinsight = get_medimageinsight_service()
        if not medimageinsight:
            raise RuntimeError("MedImageInsight service not available")

        # Step 1: Classify image with Chest X-ray labels
        logger.info("Classifying chest X-ray...")
        from backend.models.medimageinsight import MedImageInsightService
        classifications = medimageinsight.classify_image(
            image=image,
            labels=MedImageInsightService.CHEST_XRAY_LABELS
        )

        # Step 2: Generate embedding
        logger.info("Generating embedding...")
        embedding = medimageinsight.generate_embedding(image)

        # Step 3: Store embedding in Qdrant (if image_id provided)
        if image_id:
            qdrant = get_qdrant_service()
            if qdrant:
                try:
                    metadata = {
                        "modality": "Chest X-Ray",
                        "patient_name": patient_info.get("name", "Unknown"),
                        "patient_age": patient_info.get("age", 0),
                        "patient_gender": patient_info.get("gender", "Unknown"),
                        "clinical_indication": clinical_indication,
                        "findings": [c["label"] for c in classifications[:3]],  # Top 3 findings
                    }
                    await qdrant.upsert_embedding(
                        collection=MEDICAL_IMAGES_COLLECTION,
                        id=image_id,
                        vector=embedding,
                        metadata=metadata
                    )
                    logger.info(f"Stored embedding for image_id={image_id}")
                except Exception as e:
                    logger.warning(f"Failed to store embedding in Qdrant: {e}")

        # Step 4: Search for similar cases (KNN)
        similar_cases = []
        qdrant = get_qdrant_service()
        if qdrant:
            try:
                similar_results = await qdrant.search_similar(
                    collection=MEDICAL_IMAGES_COLLECTION,
                    query_vector=embedding,
                    top_k=5
                )
                similar_cases = similar_results
                logger.info(f"Found {len(similar_cases)} similar cases")
            except Exception as e:
                logger.warning(f"Failed to search similar cases: {e}")

        # Step 5: Generate findings with severity
        findings = self._generate_findings(classifications)

        # Step 6: Calculate overall confidence
        overall_confidence = sum(f["confidence"] for f in findings) / len(findings) if findings else 0.0

        # Step 7: Generate report narrative with MedGemma
        medgemma = get_medgemma_service()
        report_narrative = ""
        if medgemma:
            try:
                report_narrative = medgemma.generate_report(
                    findings=findings,
                    modality="Chest X-Ray",
                    patient_info=patient_info
                )
                logger.info("Generated report narrative")
            except Exception as e:
                logger.warning(f"Failed to generate report narrative: {e}")
                report_narrative = self._fallback_report(findings, "Chest X-Ray", patient_info)

        # Step 8: Safety check (flag if confidence < 0.7)
        requires_review = overall_confidence < 0.7

        # Step 9: Generate recommendation
        recommendation = self._generate_recommendation(findings, overall_confidence, similar_cases)

        result = {
            "findings": findings,
            "similar_cases": similar_cases,
            "recommendation": recommendation,
            "overall_confidence": overall_confidence,
            "requires_review": requires_review,
            "report_narrative": report_narrative,
            "modality": "Chest X-Ray",
            "disclaimer": DISCLAIMER
        }

        # Log audit trail
        self.log_audit(
            request=f"Chest X-ray analysis: {patient_info.get('name', 'Unknown')}",
            model="MedImageInsight + MedGemma 4B + Qdrant",
            confidence=overall_confidence,
            action="flagged_for_review" if requires_review else "processed"
        )

        return result

    async def _mri_interpretation(self, params: dict) -> dict:
        """
        Analyze brain MRI image with full pipeline.

        Uses BRAIN_MRI_LABELS for classification. Same pipeline as X-ray analysis.

        Args:
            params: Same as xray_analysis

        Returns:
            dict: Same as xray_analysis with modality="Brain MRI"
        """
        image = params.get("image")
        patient_info = params.get("patient_info", {})
        clinical_indication = params.get("clinical_indication", "Brain MRI evaluation")
        image_id = params.get("image_id", None)

        if image is None:
            raise ValueError("image parameter is required")

        if isinstance(image, bytes):
            image = Image.open(BytesIO(image))

        medimageinsight = get_medimageinsight_service()
        if not medimageinsight:
            raise RuntimeError("MedImageInsight service not available")

        # Classify with Brain MRI labels
        from backend.models.medimageinsight import MedImageInsightService
        classifications = medimageinsight.classify_image(
            image=image,
            labels=MedImageInsightService.BRAIN_MRI_LABELS
        )

        embedding = medimageinsight.generate_embedding(image)

        # Store embedding
        if image_id:
            qdrant = get_qdrant_service()
            if qdrant:
                try:
                    metadata = {
                        "modality": "Brain MRI",
                        "patient_name": patient_info.get("name", "Unknown"),
                        "patient_age": patient_info.get("age", 0),
                        "patient_gender": patient_info.get("gender", "Unknown"),
                        "clinical_indication": clinical_indication,
                        "findings": [c["label"] for c in classifications[:3]],
                    }
                    await qdrant.upsert_embedding(
                        collection=MEDICAL_IMAGES_COLLECTION,
                        id=image_id,
                        vector=embedding,
                        metadata=metadata
                    )
                except Exception as e:
                    logger.warning(f"Failed to store MRI embedding: {e}")

        # Search similar cases
        similar_cases = []
        qdrant = get_qdrant_service()
        if qdrant:
            try:
                similar_cases = await qdrant.search_similar(
                    collection=MEDICAL_IMAGES_COLLECTION,
                    query_vector=embedding,
                    top_k=5
                )
            except Exception as e:
                logger.warning(f"Failed to search similar MRI cases: {e}")

        findings = self._generate_findings(classifications)
        overall_confidence = sum(f["confidence"] for f in findings) / len(findings) if findings else 0.0

        # Generate report
        medgemma = get_medgemma_service()
        report_narrative = ""
        if medgemma:
            try:
                report_narrative = medgemma.generate_report(
                    findings=findings,
                    modality="Brain MRI",
                    patient_info=patient_info
                )
            except Exception as e:
                logger.warning(f"Failed to generate MRI report: {e}")
                report_narrative = self._fallback_report(findings, "Brain MRI", patient_info)

        requires_review = overall_confidence < 0.7
        recommendation = self._generate_recommendation(findings, overall_confidence, similar_cases)

        result = {
            "findings": findings,
            "similar_cases": similar_cases,
            "recommendation": recommendation,
            "overall_confidence": overall_confidence,
            "requires_review": requires_review,
            "report_narrative": report_narrative,
            "modality": "Brain MRI",
            "disclaimer": DISCLAIMER
        }

        self.log_audit(
            request=f"Brain MRI interpretation: {patient_info.get('name', 'Unknown')}",
            model="MedImageInsight + MedGemma 4B + Qdrant",
            confidence=overall_confidence,
            action="flagged_for_review" if requires_review else "processed"
        )

        return result

    async def _ct_review(self, params: dict) -> dict:
        """
        Analyze chest CT image with full pipeline.

        Uses CHEST_CT_LABELS for classification. Same pipeline as X-ray analysis.

        Args:
            params: Same as xray_analysis

        Returns:
            dict: Same as xray_analysis with modality="Chest CT"
        """
        image = params.get("image")
        patient_info = params.get("patient_info", {})
        clinical_indication = params.get("clinical_indication", "Chest CT evaluation")
        image_id = params.get("image_id", None)

        if image is None:
            raise ValueError("image parameter is required")

        if isinstance(image, bytes):
            image = Image.open(BytesIO(image))

        medimageinsight = get_medimageinsight_service()
        if not medimageinsight:
            raise RuntimeError("MedImageInsight service not available")

        # Classify with Chest CT labels
        from backend.models.medimageinsight import MedImageInsightService
        classifications = medimageinsight.classify_image(
            image=image,
            labels=MedImageInsightService.CHEST_CT_LABELS
        )

        embedding = medimageinsight.generate_embedding(image)

        # Store embedding
        if image_id:
            qdrant = get_qdrant_service()
            if qdrant:
                try:
                    metadata = {
                        "modality": "Chest CT",
                        "patient_name": patient_info.get("name", "Unknown"),
                        "patient_age": patient_info.get("age", 0),
                        "patient_gender": patient_info.get("gender", "Unknown"),
                        "clinical_indication": clinical_indication,
                        "findings": [c["label"] for c in classifications[:3]],
                    }
                    await qdrant.upsert_embedding(
                        collection=MEDICAL_IMAGES_COLLECTION,
                        id=image_id,
                        vector=embedding,
                        metadata=metadata
                    )
                except Exception as e:
                    logger.warning(f"Failed to store CT embedding: {e}")

        # Search similar cases
        similar_cases = []
        qdrant = get_qdrant_service()
        if qdrant:
            try:
                similar_cases = await qdrant.search_similar(
                    collection=MEDICAL_IMAGES_COLLECTION,
                    query_vector=embedding,
                    top_k=5
                )
            except Exception as e:
                logger.warning(f"Failed to search similar CT cases: {e}")

        findings = self._generate_findings(classifications)
        overall_confidence = sum(f["confidence"] for f in findings) / len(findings) if findings else 0.0

        # Generate report
        medgemma = get_medgemma_service()
        report_narrative = ""
        if medgemma:
            try:
                report_narrative = medgemma.generate_report(
                    findings=findings,
                    modality="Chest CT",
                    patient_info=patient_info
                )
            except Exception as e:
                logger.warning(f"Failed to generate CT report: {e}")
                report_narrative = self._fallback_report(findings, "Chest CT", patient_info)

        requires_review = overall_confidence < 0.7
        recommendation = self._generate_recommendation(findings, overall_confidence, similar_cases)

        result = {
            "findings": findings,
            "similar_cases": similar_cases,
            "recommendation": recommendation,
            "overall_confidence": overall_confidence,
            "requires_review": requires_review,
            "report_narrative": report_narrative,
            "modality": "Chest CT",
            "disclaimer": DISCLAIMER
        }

        self.log_audit(
            request=f"Chest CT review: {patient_info.get('name', 'Unknown')}",
            model="MedImageInsight + MedGemma 4B + Qdrant",
            confidence=overall_confidence,
            action="flagged_for_review" if requires_review else "processed"
        )

        return result

    async def _report_gen(self, params: dict) -> dict:
        """
        Generate radiology report from existing findings.

        Args:
            params: dict with keys:
                - findings (list): [{text, confidence, severity}]
                - modality (str): Imaging modality
                - patient_info (dict): Patient metadata

        Returns:
            dict with report_narrative and disclaimer
        """
        findings = params.get("findings", [])
        modality = params.get("modality", "Unknown")
        patient_info = params.get("patient_info", {})

        if not findings:
            raise ValueError("findings parameter is required")

        medgemma = get_medgemma_service()
        if medgemma:
            try:
                report_narrative = medgemma.generate_report(
                    findings=findings,
                    modality=modality,
                    patient_info=patient_info
                )
            except Exception as e:
                logger.warning(f"Failed to generate report: {e}")
                report_narrative = self._fallback_report(findings, modality, patient_info)
        else:
            report_narrative = self._fallback_report(findings, modality, patient_info)

        return {
            "report_narrative": report_narrative,
            "modality": modality,
            "disclaimer": DISCLAIMER
        }

    async def _evidence_search(self, params: dict) -> dict:
        """
        Search for similar cases by embedding.

        Args:
            params: dict with keys:
                - embedding (list[float]): Query embedding vector
                - top_k (int): Number of results (default 5)

        Returns:
            dict with similar_cases list
        """
        embedding = params.get("embedding")
        top_k = params.get("top_k", 5)

        if embedding is None:
            raise ValueError("embedding parameter is required")

        qdrant = get_qdrant_service()
        if not qdrant:
            raise RuntimeError("Qdrant service not available")

        try:
            similar_cases = await qdrant.search_similar(
                collection=MEDICAL_IMAGES_COLLECTION,
                query_vector=embedding,
                top_k=top_k
            )

            return {
                "similar_cases": similar_cases,
                "count": len(similar_cases),
                "disclaimer": DISCLAIMER
            }
        except Exception as e:
            logger.error(f"Evidence search failed: {e}")
            raise RuntimeError(f"Evidence search failed: {e}")

    def _generate_findings(self, classifications: list[dict]) -> list[dict]:
        """
        Convert MedImageInsight classifications to findings with severity.

        Args:
            classifications: List of {label, confidence} dicts

        Returns:
            list[dict]: Findings with text, confidence, severity
        """
        findings = []
        for cls in classifications:
            label = cls["label"]
            confidence = cls["confidence"]

            # Determine severity based on label and confidence
            if label.lower() in ["normal", "benign nevus", "dermatofibroma"]:
                severity = "normal"
            elif confidence > 0.7 and label.lower() in [
                "pneumonia", "cardiomegaly", "pleural effusion", "pneumothorax",
                "tumor/mass", "acute stroke", "hemorrhage", "pulmonary embolism",
                "melanoma", "basal cell carcinoma", "fracture", "dislocation"
            ]:
                severity = "high"
            elif confidence > 0.5:
                severity = "moderate"
            else:
                severity = "normal"

            findings.append({
                "text": label,
                "confidence": confidence,
                "severity": severity
            })

        return findings

    def _generate_recommendation(
        self,
        findings: list[dict],
        overall_confidence: float,
        similar_cases: list[dict]
    ) -> str:
        """
        Generate clinical recommendation based on findings and confidence.

        Args:
            findings: List of findings
            overall_confidence: Overall confidence score
            similar_cases: List of similar historical cases

        Returns:
            str: Clinical recommendation
        """
        high_severity_findings = [f for f in findings if f["severity"] == "high"]

        if overall_confidence < 0.7:
            return "MANDATORY HUMAN REVIEW: Low confidence. Radiologist verification required before clinical decisions."

        if high_severity_findings:
            high_severity_labels = [f["text"] for f in high_severity_findings]
            return f"URGENT: High-severity findings detected ({', '.join(high_severity_labels)}). Immediate radiologist review and clinical correlation recommended."

        if similar_cases and len(similar_cases) > 0:
            return f"Review findings in context of {len(similar_cases)} similar historical cases. Consider clinical correlation and follow-up if indicated."

        return "Findings noted. Clinical correlation and follow-up as clinically indicated. Radiologist review recommended."

    def _fallback_report(
        self,
        findings: list[dict],
        modality: str,
        patient_info: dict
    ) -> str:
        """
        Generate fallback report when MedGemma unavailable.

        Args:
            findings: List of findings
            modality: Imaging modality
            patient_info: Patient metadata

        Returns:
            str: Structured radiology report
        """
        patient_name = patient_info.get("name", "Unknown")
        patient_age = patient_info.get("age", "Unknown")
        patient_gender = patient_info.get("gender", "Unknown")

        findings_text = "\n".join([
            f"- {f['text']} (confidence: {f['confidence']:.2f}, severity: {f['severity']})"
            for f in findings
        ])

        report = f"""RADIOLOGY REPORT

PATIENT: {patient_name}, {patient_age} years old, {patient_gender}
MODALITY: {modality}

FINDINGS:
{findings_text}

IMPRESSION:
The above findings were identified using AI-assisted analysis. Further clinical correlation and radiologist verification are recommended before clinical decision-making.

NOTE: This is an automated preliminary report. Final interpretation requires radiologist review."""

        return report

    async def chat(self, message: str, context: dict) -> AsyncIterator[str]:
        """
        Stream chat responses about radiology analysis.

        Args:
            message: User message
            context: Conversation context

        Yields:
            str: Response tokens
        """
        # Build radiology-specific system prompt
        system_prompt = f"""You are a radiology specialist for the MedAssist AI platform.

Your role:
- Interpret medical imaging findings (X-ray, CT, MRI)
- Explain image classification results to clinicians
- Provide differential diagnoses based on imaging findings
- NEVER provide definitive diagnoses without radiologist review
- ALWAYS include disclaimer: "{DISCLAIMER}"

Context:
- Current patient: {context.get('patient_id', 'Unknown')}
- Recent imaging: {context.get('recent_imaging', 'None')}

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
_radiology_agent = None


def init_radiology_agent(anthropic_api_key: str) -> None:
    """
    Initialize global Radiology Agent.

    Args:
        anthropic_api_key: Anthropic API key for Claude
    """
    global _radiology_agent
    try:
        _radiology_agent = RadiologyAgent(anthropic_api_key)
        logger.info("Radiology Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Radiology Agent: {e}")
        _radiology_agent = None


def get_radiology_agent() -> RadiologyAgent:
    """
    Get the global Radiology Agent instance.

    Returns:
        RadiologyAgent or None if not initialized
    """
    return _radiology_agent
