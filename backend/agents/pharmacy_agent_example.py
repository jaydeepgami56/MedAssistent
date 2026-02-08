"""
Pharmacy Agent Example Usage

Demonstrates the capabilities of the Pharmacy Agent including:
1. Drug-drug interaction checking with severity classification
2. Dosage calculation based on patient parameters
3. Contraindication checking
4. Medication reconciliation
"""

import asyncio
import os
from backend.agents.pharmacy_agent import PharmacyAgent
from backend.integrations.rxnorm_client import RxNormClient
from backend.integrations.drugbank_client import DrugBankClient

# Get API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


async def example_1_drug_interaction_major():
    """
    Example 1: Check interaction between aspirin and warfarin (known major interaction).

    Expected: Major interaction - increased bleeding risk
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Drug-Drug Interaction Check (Aspirin + Warfarin)")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    # Initialize clients
    rxnorm_client = RxNormClient()
    drugbank_client = DrugBankClient()

    # Make clients globally available (simulate singleton pattern)
    import backend.integrations.rxnorm_client as rxnorm_module
    import backend.integrations.drugbank_client as drugbank_module
    rxnorm_module._rxnorm_client = rxnorm_client
    drugbank_module._drugbank_client = drugbank_client

    # Initialize agent
    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    # Check interaction
    result = await agent.execute_skill("drug_interaction", {
        "drug_names": ["aspirin", "warfarin"],
        "patient_id": "PT-001",
        "patient_conditions": ["atrial fibrillation", "coronary artery disease"]
    })

    print(f"\nSummary: {result['summary']}")
    print(f"Total interactions: {result['total_interactions']}")
    print(f"Critical interactions: {result['critical_count']}")

    print("\nInteractions:")
    for interaction in result["interactions"]:
        blocked_indicator = " [BLOCKED]" if interaction["blocked"] else ""
        print(f"  - {interaction['drug_a']} + {interaction['drug_b']}: {interaction['severity'].upper()}{blocked_indicator}")
        print(f"    Description: {interaction['description']}")
        print(f"    Source: {interaction['evidence_source']}")

    if result.get("alternatives"):
        print("\nAlternatives:")
        for alt in result["alternatives"]:
            print(f"  - Replace {alt['drug_to_replace']} with {alt['alternative']}")
            print(f"    Rationale: {alt['rationale']}")

    print(f"\n{result['disclaimer']}")

    # Cleanup
    await rxnorm_client.close()
    await drugbank_client.close()


async def example_2_triple_drug_interaction():
    """
    Example 2: Check interactions with multiple drugs (aspirin + ibuprofen + warfarin).

    Expected: Multiple interactions with varying severity
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Multiple Drug Interaction Check (3 drugs)")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    # Initialize clients
    rxnorm_client = RxNormClient()
    drugbank_client = DrugBankClient()

    import backend.integrations.rxnorm_client as rxnorm_module
    import backend.integrations.drugbank_client as drugbank_module
    rxnorm_module._rxnorm_client = rxnorm_client
    drugbank_module._drugbank_client = drugbank_client

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("drug_interaction", {
        "drug_names": ["aspirin", "ibuprofen", "warfarin"],
        "patient_id": "PT-002"
    })

    print(f"\nSummary: {result['summary']}")

    print("\nAll Interactions:")
    for interaction in result["interactions"]:
        severity_emoji = {
            "critical": "🔴",
            "major": "🟠",
            "moderate": "🟡",
            "minor": "🟢"
        }.get(interaction["severity"], "⚪")

        print(f"  {severity_emoji} {interaction['drug_a']} + {interaction['drug_b']}: {interaction['severity'].upper()}")
        print(f"     {interaction['description']}")

    print(f"\n{result['disclaimer']}")

    await rxnorm_client.close()
    await drugbank_client.close()


async def example_3_dosage_calculation():
    """
    Example 3: Calculate appropriate metformin dosage for a patient.

    Expected: Weight-based dosage with renal considerations
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Dosage Calculation (Metformin)")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("dosage_calc", {
        "drug": "metformin",
        "weight": 82,
        "age": 58,
        "renal_function": "mild impairment (eGFR 55)",
        "indication": "Type 2 diabetes mellitus"
    })

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"\nDrug: {result['drug']}")
    print(f"Dose Range: {result['dose_range']}")
    print(f"Frequency: {result['frequency']}")
    print(f"Route: {result['route']}")

    if result.get("adjustments"):
        print("\nAdjustments:")
        for adjustment in result["adjustments"]:
            print(f"  - {adjustment}")

    if result.get("warnings"):
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")

    if result.get("monitoring"):
        print("\nMonitoring Parameters:")
        for param in result["monitoring"]:
            print(f"  - {param}")

    print(f"\n{result['disclaimer']}")


async def example_4_contraindication_check():
    """
    Example 4: Check contraindications for aspirin in patient with bleeding disorder.

    Expected: Absolute contraindication detected
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Contraindication Check (Aspirin + Hemophilia)")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    # Initialize clients
    rxnorm_client = RxNormClient()
    drugbank_client = DrugBankClient()

    import backend.integrations.rxnorm_client as rxnorm_module
    import backend.integrations.drugbank_client as drugbank_module
    rxnorm_module._rxnorm_client = rxnorm_client
    drugbank_module._drugbank_client = drugbank_client

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("contraindication", {
        "drug": "aspirin",
        "conditions": ["hemophilia", "hypertension"],
        "allergies": []
    })

    print(f"\nDrug: {result['drug']}")
    print(f"Safe to use: {result['safe_to_use']}")

    if result.get("warning"):
        print(f"\nWARNING: {result['warning']}")

    print(f"\nMatched Contraindications:")
    for contra in result["contraindications"]:
        print(f"  - Type: {contra['type'].upper()}")
        print(f"    Condition: {contra['condition']}")
        print(f"    Description: {contra['description']}")
        print(f"    Severity: {contra['severity']}")

    if result.get("all_known_contraindications"):
        print(f"\nTotal known contraindications in database: {len(result['all_known_contraindications'])}")

    print(f"\n{result['disclaimer']}")

    await rxnorm_client.close()
    await drugbank_client.close()


async def example_5_medication_reconciliation():
    """
    Example 5: Reconcile home medications with hospital orders.

    Expected: Identify discrepancies and provide recommendations
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Medication Reconciliation")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    # Initialize clients
    rxnorm_client = RxNormClient()

    import backend.integrations.rxnorm_client as rxnorm_module
    rxnorm_module._rxnorm_client = rxnorm_client

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("med_reconciliation", {
        "home_medications": [
            "metformin 1000mg twice daily",
            "lisinopril 10mg daily",
            "atorvastatin 20mg daily",
            "aspirin 81mg daily"
        ],
        "hospital_medications": [
            "metformin 1000mg twice daily",
            "lisinopril 10mg daily",
            "insulin glargine 10 units at bedtime",
            "heparin 5000 units subcutaneous twice daily"
        ],
        "patient_id": "PT-003"
    })

    print(f"\nHome medications: {result['total_home']}")
    print(f"Hospital medications: {result['total_hospital']}")
    print(f"Matched: {result['total_matched']}")

    print("\nMatched Medications (continued):")
    for med in result["matched"]:
        print(f"  ✓ {med}")

    print("\nHome-Only Medications (possibly discontinued):")
    for med in result["discrepancies"]["home_only"]:
        print(f"  ⚠️  {med}")

    print("\nHospital-Only Medications (new or substitutions):")
    for med in result["discrepancies"]["hospital_only"]:
        print(f"  ⚠️  {med}")

    print("\nRecommendations:")
    print(result["recommendations"])

    print(f"\n{result['disclaimer']}")

    await rxnorm_client.close()


async def example_6_allergy_contraindication():
    """
    Example 6: Check contraindication with drug allergy.

    Expected: Absolute contraindication for documented allergy
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: Drug Allergy Contraindication")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    # Initialize clients
    rxnorm_client = RxNormClient()
    drugbank_client = DrugBankClient()

    import backend.integrations.rxnorm_client as rxnorm_module
    import backend.integrations.drugbank_client as drugbank_module
    rxnorm_module._rxnorm_client = rxnorm_client
    drugbank_module._drugbank_client = drugbank_client

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    result = await agent.execute_skill("contraindication", {
        "drug": "penicillin",
        "conditions": ["hypertension"],
        "allergies": ["penicillin", "shellfish"]
    })

    print(f"\nDrug: {result['drug']}")
    print(f"Patient Allergies: penicillin, shellfish")
    print(f"Safe to use: {result['safe_to_use']}")

    if result.get("warning"):
        print(f"\n🔴 {result['warning']}")

    print(f"\nContraindications:")
    for contra in result["contraindications"]:
        print(f"  - {contra['type'].upper()}: {contra['condition']}")
        print(f"    {contra['description']}")

    print(f"\n{result['disclaimer']}")

    await rxnorm_client.close()
    await drugbank_client.close()


async def example_7_chat_interaction():
    """
    Example 7: Interactive chat about drug information.

    Expected: Streaming response with pharmacological information
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: Chat Interaction")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Please set it to run this example.")
        return

    agent = PharmacyAgent(anthropic_api_key=ANTHROPIC_API_KEY)

    message = "What are the main drug interactions I should be aware of when prescribing warfarin?"
    context = {
        "patient_info": "72yo female with atrial fibrillation",
        "medications": ["metoprolol", "digoxin", "furosemide"]
    }

    print(f"\nUser: {message}")
    print(f"\nPharmacy Agent: ", end="", flush=True)

    async for token in agent.chat(message, context):
        print(token, end="", flush=True)

    print("\n")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("PHARMACY AGENT EXAMPLE SCENARIOS")
    print("="*80)

    # Run examples
    await example_1_drug_interaction_major()
    await example_2_triple_drug_interaction()
    await example_3_dosage_calculation()
    await example_4_contraindication_check()
    await example_5_medication_reconciliation()
    await example_6_allergy_contraindication()
    await example_7_chat_interaction()

    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
