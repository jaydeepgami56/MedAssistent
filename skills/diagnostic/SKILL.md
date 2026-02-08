# Differential Diagnosis Skill

## When to Use

Activate when analyzing symptoms to generate possible diagnoses.

**Triggers:** "diagnosis", "differential", "what could this be", "possible diagnoses",
"rule out", "DDx", "diagnostic reasoning", "pattern recognition", "rare disease"

## Process

1. **COLLECT** clinical data:
   - Chief complaint and HPI from Triage Agent
   - Vital signs and MEWS score from Monitoring Agent
   - Imaging findings from Radiology Agent
   - Lab results from FHIR/EHR
   - Relevant medical history, medications, allergies

2. **EXTRACT** key features using ClinicalBERT:
   - Symptoms and their characteristics (onset, duration, severity, quality)
   - Physical exam findings
   - Pertinent positives and negatives
   - Risk factors and red flags

3. **GENERATE** differential diagnosis list using MedGemma 27B + Claude:
   - Rank by probability (most likely first)
   - Include serious/life-threatening diagnoses that must be ruled out
   - Consider common presentations and rare diseases
   - Apply clinical reasoning frameworks (VINDICATE, SOAP-M)

4. **RECOMMEND** diagnostic tests:
   - Labs: specific tests needed to confirm/exclude each diagnosis
   - Imaging: appropriate modality for clinical question
   - Special studies: ECG, echo, biopsy, cultures as indicated
   - Prioritize by urgency and diagnostic yield

5. **PATTERN RECOGNITION**:
   - Match clinical presentation to known disease patterns
   - Query Neo4j knowledge graph (SNOMED-CT, ICD-10/11 ontology)
   - Cross-reference with similar historical cases

6. **RENDER A2UI** diagnosis panel on Canvas

## Models Used

- **MedGemma 27B**: Complex clinical reasoning for differential diagnosis generation
- **Claude API**: Diagnostic test recommendation and clinical reasoning chains
- **ClinicalBERT**: Medical entity extraction and symptom analysis
- **Neo4j**: Knowledge graph queries (SNOMED-CT, ICD-10/11 relationships)

## A2UI Output Format

Diagnosis Panel:
- **TOP:** Patient summary card (age, sex, chief complaint)
- **MAIN:** Differential diagnosis table with columns:
  - Rank (1, 2, 3...)
  - Diagnosis name
  - Probability/Likelihood (High/Medium/Low)
  - Supporting evidence (matched symptoms)
  - Against evidence (pertinent negatives)
  - Expand button for detailed reasoning
- **SIDE:** Recommended tests panel:
  - Labs (with rationale)
  - Imaging (with modality and clinical indication)
  - Urgency indicator (STAT, Routine, As needed)
- **BOTTOM:** Actions: Request Tests | Rule Out Diagnosis | Add Diagnosis | Finalize Assessment

## Safety Rules

- **ALWAYS** include life-threatening diagnoses in differential (even if low probability)
- **NEVER** present as definitive diagnosis — only differential possibilities
- **ALWAYS** include disclaimer: "AI-assisted differential — requires clinician verification and clinical judgment"
- **FLAG** rare diseases with prevalence < 1:10,000 with "RARE DISEASE" badge
- **ALWAYS** log reasoning chain for audit and learning
- **WHEN UNCERTAIN**, recommend broader workup rather than narrow focus
- For critical/emergent diagnoses (MI, stroke, PE, sepsis): auto-alert and escalate
- Display confidence scores for each diagnosis in differential

## Example

**Input:**
58-year-old male, crushing substernal chest pain radiating to left arm and jaw, onset 1 hour ago. Associated diaphoresis, nausea, dyspnea. Vitals: HR 105, BP 155/95, SpO2 96%. Hx: HTN, hyperlipidemia, smoking 30 pack-years.

**Output:**

**Differential Diagnosis:**

1. **Acute Coronary Syndrome (ACS) / NSTEMI** — HIGH probability
   - Supporting: Typical chest pain, radiation pattern, cardiac risk factors (HTN, HLD, smoking), diaphoresis
   - Against: None significant
   - Recommended: Troponin (serial q3h), ECG, CXR, consider cardiology consult

2. **Unstable Angina** — MEDIUM-HIGH probability
   - Supporting: Similar presentation to ACS, cardiac risk factors
   - Against: Would expect symptom relief with rest (not specified)
   - Recommended: Same as above, stress test if troponin negative

3. **Aortic Dissection** — MEDIUM probability (MUST RULE OUT — life-threatening)
   - Supporting: Severe chest pain, HTN, age
   - Against: No blood pressure differential between arms (not documented), pain radiation pattern more typical of ACS
   - Recommended: CT angiography chest if suspicion high, check BP both arms, d-dimer

4. **Pulmonary Embolism (PE)** — LOW-MEDIUM probability
   - Supporting: Dyspnea, chest pain
   - Against: Pain character not typical (pleuritic pain more common), no risk factors documented
   - Recommended: D-dimer, consider CT pulmonary angiography if clinical suspicion

5. **Esophageal Spasm / GERD** — LOW probability
   - Supporting: Substernal chest pain
   - Against: Radiation to arm/jaw more typical of cardiac, associated diaphoresis unusual
   - Recommended: Can consider if cardiac workup negative

**Recommended Immediate Workup:**
- Labs: Troponin I (STAT, repeat q3h x 3), CBC, BMP, lipid panel, coagulation panel
- ECG: 12-lead (STAT) — look for ST changes, T-wave inversions, Q waves
- Imaging: Chest X-ray (PA/Lateral) — assess cardiac silhouette, rule out alternative diagnoses
- Consult: Cardiology (STAT) given high suspicion for ACS

**Clinical Action:** Activate chest pain protocol, aspirin 325mg PO, oxygen if hypoxic, IV access, continuous cardiac monitoring
