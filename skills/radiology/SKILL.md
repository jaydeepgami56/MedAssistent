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
