# Drug Interaction Check Skill

## When to Use

Activate when medications are mentioned, prescribed, or need checking.

**Triggers:** "drug interaction", "medication check", "can I take", "prescribe",
"side effects", "contraindication", "polypharmacy", "medication reconciliation"

## Process

1. **EXTRACT** all medication names from conversation context
2. **RESOLVE** each to RxNorm CUI (Concept Unique Identifier) via RxNorm API
3. **QUERY** DrugBank API for known interactions between all drug pairs
4. **CROSS-REFERENCE** with patient data (via FHIR):
   - Known allergies
   - Current conditions (renal/hepatic impairment affects metabolism)
   - Age (pediatric/geriatric dosing differences)
   - Pregnancy/lactation status
5. **CLASSIFY** interaction severity:
   - **Critical:** Life-threatening. Contraindicated combination.
   - **Major:** Significant risk. Consider alternative or close monitoring.
   - **Moderate:** May require dose adjustment or monitoring.
   - **Minor:** Limited clinical significance. Awareness only.
6. **GENERATE A2UI** alert card with severity color coding

## Models Used

- **Claude API**: Reasoning about clinical context and patient-specific factors
- **RxNorm API**: Drug name normalization and CUI resolution
- **DrugBank API**: Interaction database lookup
- **FHIR R4**: Patient allergy, condition, and medication history

## A2UI Output Format

Drug Alert Card:
- Drug pair display (Drug A ⟷ Drug B)
- Severity badge (color-coded: Red/Orange/Yellow/Green)
- Interaction description
- Evidence source and reference
- Action buttons: Override (requires reason) | Suggest Alternative | Cancel Prescription

## Safety Rules

- **CRITICAL** interactions **BLOCK** workflow — requires physician override with documented reason
- **ALWAYS** include evidence links for all flagged interactions
- **NEVER** dismiss a critical interaction without human physician approval
- **LOG** all interaction checks for medication reconciliation audit
- When patient has renal/hepatic impairment: flag ALL medications metabolized by affected pathway
- Combination of 5+ medications: auto-trigger comprehensive polypharmacy review

## Example

**Input:** Patient on warfarin 5mg daily. Doctor prescribes ibuprofen 400mg TID.

**Output:**
- **CRITICAL INTERACTION** (Red)
- Warfarin + Ibuprofen (NSAIDs)
- Risk: Significantly increased risk of gastrointestinal bleeding. NSAIDs inhibit platelet function and may displace warfarin from protein binding sites, increasing anticoagulant effect.
- Source: DrugBank DB00682, RxNorm CUI 5640
- Action: BLOCKED — Requires physician override with documented clinical justification
- Suggested alternative: Acetaminophen (paracetamol) for pain management
