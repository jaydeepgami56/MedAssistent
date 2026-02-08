"""
Radiology Agent Usage Examples

Demonstrates various usage scenarios for the Radiology Agent:
1. Chest X-ray analysis with pneumonia findings
2. Brain MRI interpretation with tumor detection
3. Chest CT review for pulmonary embolism
4. Report generation from existing findings
5. KNN evidence search
6. Chat interface for radiology questions
"""

import asyncio
import os
from PIL import Image
import numpy as np

from backend.agents.radiology_agent import RadiologyAgent


def create_mock_chest_xray() -> Image.Image:
    """Create a mock chest X-ray image for testing."""
    # Create 512x512 grayscale image with some simulated pathology
    array = np.random.randint(40, 100, size=(512, 512), dtype=np.uint8)

    # Add some "abnormal" regions (darker areas simulating infiltrates)
    array[100:200, 150:250] = np.random.randint(100, 180, size=(100, 100))
    array[300:400, 200:350] = np.random.randint(120, 200, size=(100, 150))

    return Image.fromarray(array, mode='L')


def create_mock_brain_mri() -> Image.Image:
    """Create a mock brain MRI image for testing."""
    array = np.random.randint(20, 80, size=(512, 512), dtype=np.uint8)

    # Add some bright regions (simulating mass/tumor)
    array[200:280, 220:300] = np.random.randint(150, 220, size=(80, 80))

    return Image.fromarray(array, mode='L')


def create_mock_chest_ct() -> Image.Image:
    """Create a mock chest CT image for testing."""
    array = np.random.randint(30, 90, size=(512, 512), dtype=np.uint8)

    # Add linear defects (simulating PE)
    array[180:220, 200:400] = np.random.randint(140, 200, size=(40, 200))

    return Image.fromarray(array, mode='L')


async def example_1_chest_xray_analysis():
    """
    Example 1: Chest X-ray analysis with full pipeline.

    Demonstrates:
    - Image classification
    - Embedding generation and storage
    - KNN evidence search
    - Report generation
    - Safety checks
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Chest X-Ray Analysis - Suspected Pneumonia")
    print("="*80)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    # Create mock chest X-ray
    image = create_mock_chest_xray()

    params = {
        "image": image,
        "patient_info": {
            "name": "John Doe",
            "age": 45,
            "gender": "Male",
            "medical_history": "Hypertension, diabetes"
        },
        "clinical_indication": "Fever, cough, shortness of breath for 3 days",
        "image_id": "xray-2024-001"
    }

    print("\nAnalyzing chest X-ray...")
    result = await agent.execute_skill("xray_analysis", params)

    print(f"\nModality: {result['modality']}")
    print(f"Overall Confidence: {result['overall_confidence']:.3f}")
    print(f"Requires Review: {result['requires_review']}")

    print("\nFindings:")
    for i, finding in enumerate(result['findings'][:5], 1):
        print(f"  {i}. {finding['text']}: {finding['confidence']:.2f} (severity: {finding['severity']})")

    print(f"\nSimilar Cases Found: {len(result['similar_cases'])}")
    if result['similar_cases']:
        print("Top 3 similar cases:")
        for i, case in enumerate(result['similar_cases'][:3], 1):
            print(f"  {i}. Similarity: {case['score']:.3f}")
            if 'metadata' in case:
                meta = case['metadata']
                print(f"     Modality: {meta.get('modality', 'Unknown')}")
                print(f"     Findings: {', '.join(meta.get('findings', []))}")

    print(f"\nRecommendation: {result['recommendation']}")

    print("\nReport Narrative:")
    print("-" * 80)
    print(result['report_narrative'])
    print("-" * 80)

    print(f"\n{result['disclaimer']}")


async def example_2_brain_mri_interpretation():
    """
    Example 2: Brain MRI interpretation for suspected tumor.

    Demonstrates MRI analysis with different label set.
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Brain MRI Interpretation - Headache Investigation")
    print("="*80)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    image = create_mock_brain_mri()

    params = {
        "image": image,
        "patient_info": {
            "name": "Jane Smith",
            "age": 62,
            "gender": "Female",
            "medical_history": "Migraines for 15 years"
        },
        "clinical_indication": "Progressive headache, vision changes, 6 weeks duration",
        "image_id": "mri-2024-002"
    }

    print("\nInterpreting brain MRI...")
    result = await agent.execute_skill("mri_interpretation", params)

    print(f"\nModality: {result['modality']}")
    print(f"Overall Confidence: {result['overall_confidence']:.3f}")
    print(f"Requires Review: {result['requires_review']}")

    print("\nFindings:")
    for i, finding in enumerate(result['findings'][:5], 1):
        severity_color = {
            "high": "[HIGH]",
            "moderate": "[MODERATE]",
            "normal": "[NORMAL]"
        }
        print(f"  {i}. {finding['text']}: {finding['confidence']:.2f} {severity_color[finding['severity']]}")

    print(f"\nRecommendation: {result['recommendation']}")
    print(f"\n{result['disclaimer']}")


async def example_3_chest_ct_pe_evaluation():
    """
    Example 3: Chest CT for pulmonary embolism evaluation.

    Demonstrates CT analysis with critical findings.
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Chest CT - Pulmonary Embolism Evaluation")
    print("="*80)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    image = create_mock_chest_ct()

    params = {
        "image": image,
        "patient_info": {
            "name": "Bob Johnson",
            "age": 58,
            "gender": "Male",
            "medical_history": "Recent surgery, immobilization"
        },
        "clinical_indication": "Sudden onset dyspnea, chest pain, tachycardia",
        "image_id": "ct-2024-003"
    }

    print("\nReviewing chest CT...")
    result = await agent.execute_skill("ct_review", params)

    print(f"\nModality: {result['modality']}")
    print(f"Overall Confidence: {result['overall_confidence']:.3f}")
    print(f"Requires Review: {result['requires_review']}")

    print("\nFindings:")
    for i, finding in enumerate(result['findings'][:5], 1):
        print(f"  {i}. {finding['text']}: {finding['confidence']:.2f} (severity: {finding['severity']})")

    # Check for high-severity findings
    high_severity = [f for f in result['findings'] if f['severity'] == 'high']
    if high_severity:
        print("\nCRITICAL FINDINGS DETECTED:")
        for finding in high_severity:
            print(f"  - {finding['text']} (confidence: {finding['confidence']:.2f})")

    print(f"\nRecommendation: {result['recommendation']}")
    print(f"\n{result['disclaimer']}")


async def example_4_report_generation():
    """
    Example 4: Generate report from existing findings.

    Demonstrates standalone report generation capability.
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Report Generation from Findings")
    print("="*80)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    # Existing findings from previous analysis
    findings = [
        {"text": "pneumonia", "confidence": 0.85, "severity": "high"},
        {"text": "pleural effusion", "confidence": 0.72, "severity": "moderate"},
        {"text": "cardiomegaly", "confidence": 0.68, "severity": "moderate"},
        {"text": "normal", "confidence": 0.15, "severity": "normal"}
    ]

    params = {
        "findings": findings,
        "modality": "Chest X-Ray",
        "patient_info": {
            "name": "Test Patient",
            "age": 50,
            "gender": "Male"
        }
    }

    print("\nGenerating structured radiology report...")
    result = await agent.execute_skill("report_gen", params)

    print("\nReport Narrative:")
    print("-" * 80)
    print(result['report_narrative'])
    print("-" * 80)

    print(f"\n{result['disclaimer']}")


async def example_5_evidence_search():
    """
    Example 5: KNN evidence search by embedding.

    Demonstrates similarity search for historical cases.
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: KNN Evidence Search")
    print("="*80)

    # Note: This example requires Qdrant to be running and populated with embeddings
    print("\nNote: This example requires Qdrant service and existing embeddings.")
    print("To populate embeddings, run xray_analysis with image_id parameter first.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    # Create a query embedding (in real use, this would come from MedImageInsight)
    # For demonstration, use random normalized vector
    query_embedding = np.random.randn(512).tolist()
    norm = np.linalg.norm(query_embedding)
    query_embedding = [x / norm for x in query_embedding]

    params = {
        "embedding": query_embedding,
        "top_k": 5
    }

    try:
        print("\nSearching for similar cases...")
        result = await agent.execute_skill("evidence_search", params)

        print(f"\nFound {result['count']} similar cases:")
        for i, case in enumerate(result['similar_cases'], 1):
            print(f"\n  Case {i}:")
            print(f"    Similarity Score: {case['score']:.3f}")
            if 'metadata' in case:
                meta = case['metadata']
                print(f"    Modality: {meta.get('modality', 'Unknown')}")
                print(f"    Patient Age: {meta.get('patient_age', 'Unknown')}")
                print(f"    Findings: {', '.join(meta.get('findings', []))}")

        print(f"\n{result['disclaimer']}")
    except RuntimeError as e:
        print(f"\nERROR: {e}")
        print("Make sure Qdrant is running and medical_images collection exists.")


async def example_6_chat_interface():
    """
    Example 6: Chat interface for radiology questions.

    Demonstrates streaming chat responses.
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Chat Interface - Radiology Questions")
    print("="*80)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    agent = RadiologyAgent(anthropic_api_key=api_key)

    context = {
        "patient_id": "12345",
        "recent_imaging": "Chest X-Ray showing right lower lobe pneumonia"
    }

    message = "What are the typical imaging findings of pneumonia on chest X-ray, and when should follow-up imaging be considered?"

    print(f"\nUser: {message}")
    print("\nRadiology Agent: ", end="", flush=True)

    async for token in agent.chat(message, context):
        print(token, end="", flush=True)

    print("\n")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("RADIOLOGY AGENT USAGE EXAMPLES")
    print("="*80)
    print("\nThese examples demonstrate the Radiology Agent capabilities:")
    print("1. Chest X-ray analysis with full pipeline")
    print("2. Brain MRI interpretation")
    print("3. Chest CT review for PE")
    print("4. Report generation from findings")
    print("5. KNN evidence search")
    print("6. Chat interface for radiology questions")

    await example_1_chest_xray_analysis()
    await example_2_brain_mri_interpretation()
    await example_3_chest_ct_pe_evaluation()
    await example_4_report_generation()
    await example_5_evidence_search()
    await example_6_chat_interface()

    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
