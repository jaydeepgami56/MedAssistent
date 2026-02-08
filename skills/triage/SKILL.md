# Triage Assessment Skill

## When to Use

Activate when patient presents with symptoms requiring urgency assessment.

**Triggers:** "triage", "assess patient", "emergency", "priority", "how urgent",
"patient complaining of", "new patient", "walk-in", "symptoms", "pain"

## Process

1. **COLLECT** patient information:
   - Chief complaint (in patient's own words)
   - Vital signs: HR, BP, SpO2, Temperature, Respiratory Rate
   - Pain scale (1-10)
   - Symptom duration and onset
   - Relevant medical history, allergies, current medications

2. **EXTRACT** medical entities using ClinicalBERT NER:
   - Symptoms and conditions
   - Medications and allergies
   - Anatomical locations
   - Temporal indicators

3. **CHECK RED FLAGS** (auto-escalate if ANY present):
   - **Cardiac:** chest pain, palpitations, syncope, cardiac arrest
   - **Respiratory:** severe dyspnea, stridor, SpO2 < 90%, respiratory arrest
   - **Neurological:** altered consciousness, stroke (FAST+), seizure, GCS < 9
   - **Trauma:** severe hemorrhage, mechanism of injury, burns > 20% BSA
   - **Other:** anaphylaxis, sepsis (qSOFA ≥ 2), overdose, obstetric emergency

4. **CALCULATE ESI** (Emergency Severity Index 1-5):
   - **ESI-1 Resuscitation:** Immediate life-threatening condition requiring aggressive intervention
   - **ESI-2 Emergency:** High risk situation OR severe pain/distress OR altered mental status
   - **ESI-3 Urgent:** Stable but needs multiple resources (labs + imaging + IV, etc.)
   - **ESI-4 Semi-urgent:** Stable, single resource expected (X-ray OR lab OR simple procedure)
   - **ESI-5 Non-urgent:** No resources expected (prescription refill, simple wound check)

5. **GENERATE A2UI** triage card on Canvas:
   - Color-coded ESI badge (Red/Orange/Yellow/Green/Blue)
   - Patient summary with symptom list
   - Red flag alerts (if detected)
   - Routing recommendation
   - Estimated wait time

6. **ROUTE** patient to appropriate department/specialist

## Models Used

- **ClinicalBERT** (110M): Medical entity extraction (symptoms, conditions, medications)
- **Claude API**: Clinical reasoning chain for ESI score determination

## A2UI Output Format

Generate triage card with surfaceUpdate + beginRendering:
- Header: Patient name, age, gender
- ESI badge with color coding
- Chief complaint summary
- Vital signs grid
- Red flag alerts (if any, in red)
- Routing: Recommended department/specialist
- Actions: Confirm | Override ESI | Add Notes | Escalate

## Safety Rules

- **ALWAYS** escalate ESI 1-2 to human clinician immediately (auto-alert)
- **NEVER** provide definitive diagnosis — only urgency classification
- **NEVER** downgrade an ESI score without explicit clinician override
- **ALWAYS** include disclaimer: "AI-assisted triage — requires clinician verification"
- **ALWAYS** log full reasoning chain for audit trail
- **WHEN UNCERTAIN**, escalate urgency level (fail-safe UP, never DOWN)
- Red flags detected = minimum ESI-2, regardless of other factors

## Example

**Input:**
"67-year-old female, chief complaint: crushing chest pain radiating to left arm,
onset 30 minutes ago, diaphoretic, nauseous. HR 110, BP 90/60, SpO2 94%, Temp 36.8°C, RR 22."

**Output:**
- **ESI-1 (Resuscitation)** — RED
- Red Flags: chest pain + radiation, hypotension (BP 90/60), tachycardia (HR 110), desaturation (SpO2 94%), tachypnea (RR 22)
- Route: Resuscitation bay — IMMEDIATE
- Auto-alert: Attending physician + cardiology
- Reasoning: Multiple life-threatening red flags consistent with acute MI. Hemodynamically unstable.
