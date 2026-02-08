# MedAssist AI — SKILL.md Files

Complete SKILL.md definitions for all medical agents.

---

## 1. Triage Assessment Skill

**File:** `skills/triage/SKILL.md`

```markdown
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
```

---

## 2. Medical Image Analysis Skill

**File:** `skills/radiology/SKILL.md`

```markdown
# Medical Image Analysis Skill

## When to Use

Activate when user uploads or references medical images.

**Triggers:** "analyze", "X-ray", "MRI", "CT scan", "radiology", "scan", "image",
"what does this show", "report", "findings", "ultrasound", "mammogram", "dermoscopy"

## Process

1. **IDENTIFY** imaging modality:
   - Route image to MedSigLIP for fast classification
   - Supported: X-ray, MRI, CT, ultrasound, dermoscopy, OCT, fundus, histopathology, mammography

2. **ENCODE** image:
   - Pass to MedImageInsight for embedding generation
   - Store embedding in Qdrant vector database for future KNN queries

3. **CLASSIFY** with zero-shot against modality-specific labels:

   **Chest X-ray:**
   `["normal", "pneumonia", "cardiomegaly", "pleural effusion", "atelectasis",
     "consolidation", "pneumothorax", "fracture", "mass", "edema"]`

   **Brain MRI:**
   `["normal", "tumor/mass", "acute stroke", "hemorrhage", "cerebral atrophy",
     "MS lesion", "hydrocephalus", "abscess"]`

   **Chest CT:**
   `["normal", "pulmonary nodule", "mass", "ground-glass opacity",
     "consolidation", "lymphadenopathy", "pleural effusion", "pneumothorax"]`

   **Musculoskeletal:**
   `["normal", "fracture", "dislocation", "degenerative arthritis",
     "soft tissue mass", "osteoporosis", "osteomyelitis"]`

   **Dermatology:**
   `["benign nevus", "melanoma", "basal cell carcinoma", "squamous cell carcinoma",
     "actinic keratosis", "dermatofibroma", "vascular lesion"]`

4. **SEARCH** for evidence:
   - KNN image-image search in Qdrant vector DB
   - Retrieve 3-5 similar historical cases with known diagnoses
   - Include similarity scores for transparency

5. **GENERATE REPORT** using MedGemma 4B:
   - Structured findings narrative
   - Clinical impression
   - Recommendation for follow-up or additional imaging

6. **RENDER A2UI** split-panel radiology report on Canvas

## Models Used

- **MedSigLIP** (400M): Fast modality routing and image triage
- **MedImageInsight** (0.61B): Zero-shot classification + image embedding + KNN evidence search
- **MedGemma 4B**: Report narrative generation from findings
- **Qdrant**: Vector similarity search for evidence-based case matching

## A2UI Output Format

Split-panel report:
- **LEFT:** Patient info card, Findings list (severity dot + text + confidence%), Classification results
- **RIGHT:** Similar cases card (thumbnails + similarity scores), Recommendation card, Action buttons
- **BOTTOM:** Disclaimer

## Safety Rules

- **ALWAYS** include: "AI-assisted analysis — requires radiologist review"
- **ALWAYS** display confidence scores (AUC) for ALL findings
- **FLAG** findings with confidence < 0.7 for **MANDATORY** human review
- **NEVER** use as definitive diagnosis
- **LOG** all analyses: model version, confidence scores, clinician action, timestamp
- For critical findings (pneumothorax, stroke, hemorrhage): auto-alert radiologist on-call

## Example

**Input:** Chest X-ray PA view, 45-year-old male

**Output:**
- Finding 1: Bilateral lower lobe infiltrates consistent with pneumonia — **94% confidence** (HIGH)
- Finding 2: Mild cardiomegaly — **87% confidence** (MODERATE)
- Finding 3: No pneumothorax — **96% confidence** (NORMAL)
- Finding 4: Bilateral costophrenic angle blunting — **82% confidence** (MODERATE)
- Similar cases: 4 found (similarity range: 0.87-0.93)
- Recommendation: Correlate with CT for further evaluation. Suggest cardiology consult.
```

---

## 3. Drug Interaction Check Skill

**File:** `skills/pharmacy/SKILL.md`

```markdown
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
```

---

## 4. Vital Sign Monitoring Skill

**File:** `skills/monitoring/SKILL.md`

```markdown
# Patient Vital Sign Monitoring Skill

## When to Use

Activate for continuous patient monitoring or when vital signs are reported.

**Triggers:** "monitor vitals", "vital signs", "heart rate", "blood pressure",
"oxygen saturation", "MEWS", "early warning", "deterioration"

## Process

1. **RECEIVE** vital sign data (from IoT monitors or manual entry):
   HR, BP (systolic/diastolic), SpO2, Temperature, Respiratory Rate
2. **CALCULATE** Modified Early Warning Score (MEWS):
   - HR: <40 or >130 = 3pts, 41-50 or 111-130 = 2pts, 51-100 = 0pts, 101-110 = 1pt
   - BP systolic: <70 = 3pts, 71-80 = 2pts, 81-100 = 1pt, 101-199 = 0pts, >200 = 2pts
   - RR: <9 = 2pts, 9-14 = 0pts, 15-20 = 1pt, 21-29 = 2pts, >29 = 3pts
   - Temp: <35 = 2pts, 35-38.4 = 0pts, >38.5 = 2pts
3. **DETECT** anomalies: sudden changes from patient baseline
4. **TRACK** trends over time (6-hour rolling window)
5. **ALERT** based on MEWS threshold:
   - MEWS 0-2: Normal — routine monitoring
   - MEWS 3-4: Increased concern — notify nurse, increase monitoring frequency
   - MEWS 5+: Critical — immediate medical review, call attending
6. **RENDER** A2UI vitals dashboard with real-time updates

## Models Used

- **Time-series ML**: Anomaly detection and trend analysis
- **Claude API**: Natural language alerting and clinical context

## Safety Rules

- MEWS ≥ 5 triggers **AUTOMATIC** attending physician notification
- **NEVER** reduce alert level without clinician acknowledgment
- Maintain 6-hour rolling trend for pattern detection
- SpO2 < 90% = immediate alert regardless of MEWS score
```

---

## 5. Clinical Documentation Skill

**File:** `skills/documentation/SKILL.md`

```markdown
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

## Safety Rules

- **ALWAYS** present as draft for clinician review and editing
- **NEVER** finalize without explicit clinician approval
- Include all contributing agent sources for traceability
```

---

## 6. Research & Evidence Skill

**File:** `skills/research/SKILL.md`

```markdown
# Clinical Evidence & Research Skill

## When to Use

Activate when clinical evidence, guidelines, or research is needed.

**Triggers:** "guidelines", "evidence", "research", "clinical trial", "PubMed",
"latest treatment", "best practice", "what does the evidence say"

## Process

1. **FORMULATE** search query from clinical question
2. **SEARCH** across:
   - PubMed API (peer-reviewed literature)
   - ClinicalTrials.gov (active/recruiting trials)
   - UpToDate / clinical guidelines databases
3. **FILTER** by relevance, recency, evidence level (meta-analysis > RCT > cohort > case)
4. **SYNTHESIZE** findings into concise summary using Claude API
5. **MATCH** relevant clinical trials to patient demographics
6. **RENDER** evidence cards on A2UI Canvas

## Safety Rules

- **ALWAYS** cite sources with publication details
- **ALWAYS** note evidence level/grade
- **NEVER** present as clinical recommendation — present as "evidence suggests..."
- Flag conflicting evidence when found
```

---

## Project File Structure

```
~/.openclaw/workspace/skills/
├── triage/
│   ├── SKILL.md          # Triage assessment skill (above)
│   └── skill.json        # {"name":"triage","version":"1.0","agent":"triage"}
├── radiology/
│   ├── SKILL.md          # Medical image analysis skill (above)
│   └── skill.json
├── pharmacy/
│   ├── SKILL.md          # Drug interaction check skill (above)
│   └── skill.json
├── diagnostic/
│   ├── SKILL.md          # Differential diagnosis skill
│   └── skill.json
├── monitoring/
│   ├── SKILL.md          # Vital sign monitoring skill (above)
│   └── skill.json
├── documentation/
│   ├── SKILL.md          # Clinical documentation skill (above)
│   └── skill.json
└── research/
    ├── SKILL.md          # Research & evidence skill (above)
    └── skill.json
```
