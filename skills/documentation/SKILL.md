# Clinical Documentation Skill

## When to Use

Activate when clinical notes, summaries, or reports are needed.

**Triggers:** "clinical note", "SOAP note", "discharge summary", "documentation",
"write up", "summarize encounter", "ICD code", "referral letter"

## Process

1. **COLLECT** data from:
   - Chat/conversation transcript
   - Triage Agent output (ESI, symptoms)
   - Radiology Agent output (findings, reports)
   - Pharmacy Agent output (medications, interactions)
   - Monitoring Agent output (vitals, trends)
   - FHIR patient record
2. **GENERATE** SOAP format note using Claude API:
   - S (Subjective): Patient's words, HPI, symptoms
   - O (Objective): Vitals, exam, labs, imaging
   - A (Assessment): Diagnosis, differential dx
   - P (Plan): Treatment, meds, follow-up, referrals
3. **SUGGEST** ICD-10 codes from Assessment section
4. **RENDER** editable A2UI form on Canvas

## Models Used

- **Claude API**: SOAP note generation and medical summarization
- **FHIR R4**: Patient history and encounter data retrieval

## A2UI Output Format

SOAP Editor:
- Editable text areas for each SOAP section (S, O, A, P)
- ICD-10 code suggestions with autocomplete
- Patient header with demographics
- Action buttons: Save Draft | Finalize | Export to EHR | Cancel
- Version history sidebar

## Safety Rules

- **ALWAYS** present as draft for clinician review and editing
- **NEVER** finalize without explicit clinician approval
- Include all contributing agent sources for traceability
- **LOG** all documentation actions: created, edited, finalized, exported
- **NEVER** auto-populate without showing sources
- Display disclaimer: "AI-generated draft — requires clinician review and signature"

## Example

**Input:** Patient encounter data from triage, vitals, imaging

**Output SOAP Note:**

**S (Subjective):**
45-year-old male presents with acute onset crushing chest pain radiating to left arm, onset 2 hours ago. Associated symptoms: diaphoresis, nausea, shortness of breath. Denies prior cardiac history. No known drug allergies.

**O (Objective):**
Vitals: HR 110 bpm, BP 145/90 mmHg, SpO2 95% on room air, Temp 37.1°C, RR 20/min
Physical: Diaphoretic, anxious, no JVD, lung fields clear, S1/S2 regular, no murmurs
Labs: Troponin elevated at 0.8 ng/mL (pending serial)
Imaging: Chest X-ray shows no acute cardiopulmonary process, no pneumothorax

**A (Assessment):**
Acute coronary syndrome (ACS), likely NSTEMI given troponin elevation and clinical presentation. High risk for adverse cardiac events.

**P (Plan):**
1. Cardiology consult — STAT
2. Serial troponins q3h x 3
3. Aspirin 325mg PO, Clopidogrel 300mg loading dose
4. Heparin drip per protocol
5. Admit to CCU for monitoring and potential catheterization
6. NPO after midnight

**ICD-10 Suggestions:**
- I21.4 — Non-ST elevation myocardial infarction (NSTEMI)
- R07.9 — Chest pain, unspecified
