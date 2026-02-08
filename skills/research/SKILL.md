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

## Models Used

- **Claude API**: Query formulation and evidence synthesis
- **PubMed API**: Literature search (peer-reviewed publications)
- **ClinicalTrials.gov API**: Active trial matching

## A2UI Output Format

Evidence Panel:
- Search query display
- Evidence cards (sorted by relevance):
  - Title + authors + journal + year
  - Evidence level badge (meta-analysis/RCT/cohort/case)
  - Abstract summary (3-4 sentences)
  - Key findings highlight
  - Link to full text
- Clinical trial cards (if applicable):
  - Trial phase, status (recruiting/active/completed)
  - Inclusion/exclusion criteria
  - Location and contact
- Action buttons: Export References | Add to Case | Request Full Text

## Safety Rules

- **ALWAYS** cite sources with publication details (authors, journal, year, PMID)
- **ALWAYS** note evidence level/grade (IA, IB, IIA, IIB, III, etc.)
- **NEVER** present as clinical recommendation — present as "evidence suggests..."
- Flag conflicting evidence when found
- **NEVER** recommend off-label use without explicit evidence citation
- Display disclaimer: "For informational purposes — clinical decisions require physician judgment"

## Example

**Input:** "What is the latest evidence for anticoagulation in atrial fibrillation?"

**Output:**

**Evidence Summary:**
Recent meta-analyses and RCTs support direct oral anticoagulants (DOACs) as first-line therapy for stroke prevention in non-valvular atrial fibrillation.

**Top Evidence:**

1. **Meta-analysis (Level IA)** — Ruff CT et al., Lancet 2014
   - Pooled analysis of 71,683 patients across 4 RCTs (RE-LY, ROCKET-AF, ARISTOTLE, ENGAGE-AF)
   - DOACs vs warfarin: 19% reduction in stroke/systemic embolism, 10% reduction in mortality
   - Similar major bleeding but 52% reduction in intracranial hemorrhage
   - PMID: 24315724

2. **RCT (Level IB)** — Granger CB et al., NEJM 2011 (ARISTOTLE Trial)
   - Apixaban vs warfarin in 18,201 patients
   - 21% relative risk reduction in stroke/systemic embolism (HR 0.79, p<0.01)
   - 31% reduction in major bleeding
   - PMID: 21870978

**Clinical Trials:**
- NCT04856722: OCEAN trial — Edoxaban vs warfarin in patients >80 years (recruiting)
- Eligibility: Age >80, non-valvular AF, CHA2DS2-VASc ≥2

**Guideline Recommendation (AHA/ACC/HRS 2019):**
DOACs preferred over warfarin for stroke prevention in non-valvular AF (Class I, Level A)
