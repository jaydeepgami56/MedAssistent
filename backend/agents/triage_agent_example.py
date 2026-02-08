"""
Triage Agent Usage Examples

Demonstrates ESI scoring, red flag detection, and patient routing.
"""

import asyncio
import os
from backend.agents.triage_agent import TriageAgent
from backend.models.clinical_bert import init_clinical_bert


async def main():
    """Run triage agent examples."""
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in environment")
        print("Set with: export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Initialize ClinicalBERT service
    print("Initializing ClinicalBERT service...")
    init_clinical_bert(api_key)

    # Create Triage Agent
    print("Initializing Triage Agent...\n")
    agent = TriageAgent(api_key)

    # Display agent info
    info = agent.get_info()
    print(f"Agent: {info['name']} (ID: {info['agent_id']})")
    print(f"Status: {info['status']}")
    print(f"Skills: {', '.join(info['skills'])}")
    print(f"Models: {', '.join(info['models_used'])}")
    print(f"Color: {info['color']} | Icon: {info['icon']}")
    print("\n" + "="*80 + "\n")

    # Example 1: Critical case - Chest pain (ESI-1)
    print("EXAMPLE 1: Critical Chest Pain (ESI-1)")
    print("-" * 40)
    params1 = {
        "complaint": "67-year-old female with crushing chest pain radiating to left arm, onset 30 minutes ago, diaphoretic, nauseous",
        "vitals": {
            "hr": 110,
            "bp_sys": 90,
            "bp_dia": 60,
            "spo2": 94,
            "temp": 36.8,
            "rr": 22
        },
        "pain_scale": 9,
        "duration": "30 minutes",
        "history": "Hypertension, diabetes, hyperlipidemia",
        "allergies": ["Penicillin"],
        "medications": ["Metformin", "Lisinopril", "Atorvastatin"]
    }

    result1 = await agent.execute_skill("esi_scoring", params1)

    print(f"ESI Score: {result1['esi_score']} - {result1['esi_label']}")
    print(f"Red Flags ({len(result1['red_flags'])}):")
    for flag in result1['red_flags']:
        print(f"  - {flag}")
    print(f"Routing: {result1['routing']}")
    print(f"Wait Time: {result1['wait_time']}")
    print(f"Confidence: {result1['confidence']:.2f}")
    print(f"Reasoning: {result1['reasoning'][:200]}...")
    print(f"\n{result1['disclaimer']}")
    print("\n" + "="*80 + "\n")

    # Example 2: Respiratory distress (ESI-2)
    print("EXAMPLE 2: Severe Respiratory Distress (ESI-2)")
    print("-" * 40)
    params2 = {
        "complaint": "45-year-old male with severe shortness of breath, unable to speak in full sentences",
        "vitals": {
            "hr": 120,
            "bp_sys": 140,
            "bp_dia": 85,
            "spo2": 85,
            "temp": 37.2,
            "rr": 32
        },
        "pain_scale": 7,
        "duration": "2 hours",
        "history": "Asthma, COPD",
        "allergies": [],
        "medications": ["Albuterol inhaler", "Advair"]
    }

    result2 = await agent.execute_skill("esi_scoring", params2)

    print(f"ESI Score: {result2['esi_score']} - {result2['esi_label']}")
    print(f"Red Flags ({len(result2['red_flags'])}):")
    for flag in result2['red_flags']:
        print(f"  - {flag}")
    print(f"Routing: {result2['routing']}")
    print(f"Wait Time: {result2['wait_time']}")
    print("\n" + "="*80 + "\n")

    # Example 3: Urgent but stable (ESI-3)
    print("EXAMPLE 3: Fever and Cough - Urgent (ESI-3)")
    print("-" * 40)
    params3 = {
        "complaint": "32-year-old male with fever, productive cough, and body aches for 3 days",
        "vitals": {
            "hr": 95,
            "bp_sys": 130,
            "bp_dia": 80,
            "spo2": 96,
            "temp": 38.5,
            "rr": 18
        },
        "pain_scale": 4,
        "duration": "3 days",
        "history": "No significant medical history",
        "allergies": [],
        "medications": []
    }

    result3 = await agent.execute_skill("esi_scoring", params3)

    print(f"ESI Score: {result3['esi_score']} - {result3['esi_label']}")
    print(f"Red Flags: {len(result3['red_flags'])}")
    print(f"Routing: {result3['routing']}")
    print(f"Wait Time: {result3['wait_time']}")
    print("\n" + "="*80 + "\n")

    # Example 4: Minor injury (ESI-4/5)
    print("EXAMPLE 4: Minor Ankle Sprain - Semi-urgent (ESI-4)")
    print("-" * 40)
    params4 = {
        "complaint": "28-year-old male with minor ankle sprain from playing basketball yesterday",
        "vitals": {
            "hr": 75,
            "bp_sys": 125,
            "bp_dia": 78,
            "spo2": 99,
            "temp": 37.0,
            "rr": 14
        },
        "pain_scale": 4,
        "duration": "1 day",
        "history": "Healthy, no chronic conditions",
        "allergies": [],
        "medications": []
    }

    result4 = await agent.execute_skill("esi_scoring", params4)

    print(f"ESI Score: {result4['esi_score']} - {result4['esi_label']}")
    print(f"Red Flags: {len(result4['red_flags'])}")
    print(f"Routing: {result4['routing']}")
    print(f"Wait Time: {result4['wait_time']}")
    print("\n" + "="*80 + "\n")

    # Example 5: Red flag detection only
    print("EXAMPLE 5: Red Flag Detection Only")
    print("-" * 40)
    red_flag_params = {
        "complaint": "Patient with sudden severe headache, worst headache of life",
        "vitals": {
            "hr": 88,
            "bp_sys": 185,
            "bp_dia": 95,
            "spo2": 98,
            "temp": 36.9,
            "rr": 18
        },
        "pain_scale": 10
    }

    result5 = await agent.execute_skill("red_flag_detection", red_flag_params)

    print(f"Red Flags Detected: {result5['count']}")
    for flag in result5['red_flags']:
        print(f"  - {flag}")
    print(f"Requires Escalation: {result5['requires_escalation']}")
    print("\n" + "="*80 + "\n")

    # Example 6: Emergency alert
    print("EXAMPLE 6: Emergency Alert Generation")
    print("-" * 40)
    alert_params = {
        "esi_score": 1,
        "complaint": "Cardiac arrest in waiting room",
        "red_flags": ["Cardiac: cardiac arrest", "Vital sign: no pulse"]
    }

    result6 = await agent.execute_skill("emergency_alert", alert_params)

    print(f"Alert Level: {result6['alert_level']}")
    print(f"Requires Notification: {result6['requires_notification']}")
    print(f"Notify: {', '.join(result6['notify_roles'])}")
    print(f"Message: {result6['message']}")
    print("\n" + "="*80 + "\n")

    # Example 7: Chat interaction
    print("EXAMPLE 7: Chat Interaction")
    print("-" * 40)
    print("User: What is the Emergency Severity Index?\n")
    print("Agent: ", end="", flush=True)

    chat_context = {"patient_id": "P12345", "recent_assessments": "None"}
    async for token in agent.chat("What is the Emergency Severity Index?", chat_context):
        print(token, end="", flush=True)

    print("\n\n" + "="*80)
    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
