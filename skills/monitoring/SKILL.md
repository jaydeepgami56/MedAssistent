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

## A2UI Output Format

Vitals Dashboard:
- 3x2 grid of vital sign cards (HR, BP, SpO2, Temp, RR, MEWS)
- Color-coded badges (green/yellow/orange/red)
- 6-hour trend chart for each vital
- Alert banner for critical values
- Actions: Acknowledge Alert | Escalate | View History

## Safety Rules

- MEWS ≥ 5 triggers **AUTOMATIC** attending physician notification
- **NEVER** reduce alert level without clinician acknowledgment
- Maintain 6-hour rolling trend for pattern detection
- SpO2 < 90% = immediate alert regardless of MEWS score
- **ALWAYS** log all vital sign readings with timestamp for audit trail
- **WHEN UNCERTAIN** about anomaly, escalate to human review

## Example

**Input:**
HR 125 bpm, BP 85/55 mmHg, SpO2 91%, Temp 38.7°C, RR 24/min

**Output:**
- **MEWS Score: 6** (CRITICAL)
- HR: 125 bpm (2 points) — Tachycardic
- BP: 85/55 mmHg (1 point) — Hypotensive
- RR: 24/min (2 points) — Tachypneic
- Temp: 38.7°C (2 points) — Febrile
- SpO2: 91% — ALERT (below 92% threshold)
- **AUTOMATIC ESCALATION:** Attending physician notified
- Trend: Deteriorating over last 2 hours
- Action Required: Immediate clinical review
