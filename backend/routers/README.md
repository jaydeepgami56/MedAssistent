# MedAssist AI REST API Endpoints

This directory contains FastAPI routers for the MedAssist AI platform.

## Implemented Endpoints

### Core Agent Endpoints

#### `GET /agents`
List all registered agents with their metadata.

**Response:**
```json
[
  {
    "agent_id": "triage",
    "name": "Triage Agent",
    "status": "Active",
    "skills": ["esi_scoring", "red_flag_detection", "patient_routing", "emergency_alert"],
    "queue": 0,
    "models_used": ["ClinicalBERT", "Claude API"],
    "color": "#ef4444",
    "icon": "🚨"
  },
  ...
]
```

#### `GET /agents/{agent_id}`
Get details for a specific agent.

**Path Parameters:**
- `agent_id`: Agent identifier (triage, radiology, diagnostic, pharmacy, monitoring, documentation, research, coordinator)

**Response:** Same as individual agent object above

**Error Responses:**
- `404`: Agent not found

#### `POST /agents/{agent_id}/chat`
Stream chat responses from an agent using Server-Sent Events (SSE).

**Request Body:**
```json
{
  "message": "What are the signs of sepsis?",
  "context": {
    "patient_id": "P123",
    "history": []
  }
}
```

**Response:** Server-Sent Events stream
```
data: Sepsis is a life-threatening...
data: Common signs include...
data:

AI-assisted — requires clinician verification
```

**Error Responses:**
- `404`: Agent not found

#### `POST /agents/{agent_id}/execute`
Execute a specific skill on an agent.

**Request Body:**
```json
{
  "skill_name": "esi_scoring",
  "params": {
    "chief_complaint": "Chest pain",
    "symptoms": ["chest pain", "dyspnea"],
    "vitals": {
      "heart_rate": 110,
      "bp": "140/90"
    }
  }
}
```

**Response:** Skill-specific result dict

**Error Responses:**
- `404`: Agent not found
- `400`: Invalid skill name
- `500`: Skill execution failed

#### `GET /agents/skills/list`
List all available skills across all agents.

**Response:**
```json
{
  "triage": ["esi_scoring", "red_flag_detection", "patient_routing", "emergency_alert"],
  "radiology": ["xray_analysis", "mri_interpretation", "ct_review", "report_gen", "evidence_search"],
  ...
}
```

### Domain-Specific Endpoints

#### `POST /agents/triage/assess`
Submit patient data for triage assessment and ESI scoring.

**Request Body:**
```json
{
  "chief_complaint": "Chest pain",
  "symptoms": ["chest pain", "shortness of breath", "diaphoresis"],
  "vitals": {
    "heart_rate": 110,
    "bp": "140/90",
    "spo2": 94,
    "respiratory_rate": 24,
    "temperature": 37.2
  },
  "history": {
    "diabetes": true,
    "hypertension": true
  },
  "allergies": ["penicillin"]
}
```

**Response:**
```json
{
  "esi_level": 2,
  "red_flags": ["chest pain with cardiac risk factors", "elevated heart rate"],
  "routing": "Emergency",
  "requires_review": false,
  "confidence": 0.89
}
```

**Error Responses:**
- `503`: Triage agent not available
- `500`: Assessment failed

#### `POST /agents/radiology/analyze`
Submit an image for radiology analysis.

**Request:** Multipart form data
- `file`: Image file (DICOM, PNG, JPG)
- `study_type`: Type of study (chest_xray, mri, ct_scan) - default: chest_xray
- `patient_id`: Optional patient identifier

**Response:**
```json
{
  "findings": [
    {
      "location": "Right lower lobe",
      "finding": "Opacity consistent with pneumonia",
      "severity": "moderate"
    }
  ],
  "impression": "Right lower lobe pneumonia. No pleural effusion.",
  "confidence": 0.82,
  "knn_evidence": [
    {
      "similarity": 0.91,
      "case_id": "C12345",
      "diagnosis": "Community-acquired pneumonia"
    }
  ],
  "requires_review": false
}
```

**Error Responses:**
- `503`: Radiology agent not available
- `400`: Invalid or empty file
- `500`: Analysis failed

#### `POST /agents/pharmacy/check`
Check drug interactions and contraindications.

**Request Body:**
```json
{
  "drug_names": ["warfarin", "aspirin", "ibuprofen"],
  "patient_id": "P123",
  "patient_data": {
    "age": 65,
    "weight": 70,
    "conditions": ["atrial fibrillation", "hypertension"]
  }
}
```

**Response:**
```json
{
  "severity": "critical",
  "interactions": [
    {
      "drugs": ["warfarin", "ibuprofen"],
      "severity": "major",
      "description": "Increased risk of bleeding",
      "action": "Avoid combination or monitor closely"
    }
  ],
  "contraindications": [],
  "requires_review": true,
  "confidence": 0.95
}
```

**Error Responses:**
- `503`: Pharmacy agent not available
- `500`: Check failed

#### `POST /agents/monitoring/vitals`
Submit vital signs for monitoring and MEWS score calculation.

**Request Body:**
```json
{
  "heart_rate": 110,
  "systolic_bp": 140,
  "diastolic_bp": 90,
  "respiratory_rate": 24,
  "temperature": 38.5,
  "spo2": 92,
  "avpu": "Alert"
}
```

**Response:**
```json
{
  "mews_score": 5,
  "alert_level": "moderate",
  "components": {
    "heart_rate": 2,
    "systolic_bp": 1,
    "respiratory_rate": 1,
    "temperature": 1,
    "avpu": 0
  },
  "requires_escalation": true,
  "confidence": 1.0
}
```

**Error Responses:**
- `503`: Monitoring agent not available
- `500`: Calculation failed

#### `POST /agents/documentation/generate`
Generate clinical documentation (SOAP notes).

**Request Body:**
```json
{
  "encounter_data": {
    "patient_id": "P123",
    "chief_complaint": "Chest pain",
    "history": "65yo M with HTN, DM presenting with chest pain x2 hours",
    "exam": "VS stable. Chest clear. Heart RRR no murmurs.",
    "vitals": {...},
    "labs": {...},
    "assessment": "Chest pain, likely cardiac"
  }
}
```

**Response:**
```json
{
  "subjective": "65yo M with history of HTN and DM...",
  "objective": "VS: HR 80, BP 140/90...",
  "assessment": "1. Chest pain - r/o ACS\n2. Hypertension - controlled\n3. Diabetes - stable",
  "plan": "1. EKG, troponin, CXR\n2. ASA 325mg...",
  "icd10_codes": ["R07.9", "I10", "E11.9"],
  "confidence": 0.85
}
```

**Error Responses:**
- `503`: Documentation agent not available
- `500`: Generation failed

#### `POST /agents/research/search`
Search clinical evidence and guidelines.

**Request Body:**
```json
{
  "query": "acute coronary syndrome management guidelines 2025"
}
```

**Response:**
```json
{
  "articles": [
    {
      "pmid": "12345678",
      "title": "2024 ACC/AHA Guidelines for ACS Management",
      "authors": "Smith J, et al.",
      "journal": "Circulation",
      "year": 2024,
      "abstract": "...",
      "evidence_level": "1A"
    }
  ],
  "guidelines": [
    {
      "organization": "ACC/AHA",
      "title": "Acute Coronary Syndrome Guidelines",
      "year": 2024,
      "recommendations": ["..."]
    }
  ],
  "confidence": 0.92
}
```

**Error Responses:**
- `503`: Research agent not available
- `500`: Search failed

## Error Handling

All endpoints follow consistent error handling patterns:

1. **404 Not Found**: Resource (agent) doesn't exist
2. **400 Bad Request**: Invalid input (missing fields, invalid skill name, empty file)
3. **500 Internal Server Error**: Execution failed, wrapped exception
4. **503 Service Unavailable**: Agent not initialized (missing API key or dependencies)

Error responses include a `detail` field with a human-readable message.

## Testing

Run the test suite to verify all endpoints:

```bash
# Test endpoint registration
python test_endpoints.py

# Test API signatures and models
python test_api_signatures.py

# Test integration (requires initialized agents)
python test_api_integration.py
```

## Usage Examples

### Using curl

```bash
# List all agents
curl http://localhost:8000/agents

# Get triage agent details
curl http://localhost:8000/agents/triage

# Execute triage assessment
curl -X POST http://localhost:8000/agents/triage/assess \
  -H "Content-Type: application/json" \
  -d '{"chief_complaint": "Chest pain", "symptoms": ["chest pain"], "vitals": {"heart_rate": 110}}'

# Chat with diagnostic agent (SSE stream)
curl -X POST http://localhost:8000/agents/diagnostic/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the differential diagnoses for chest pain?"}'

# Upload chest x-ray for analysis
curl -X POST http://localhost:8000/agents/radiology/analyze \
  -F "file=@chest_xray.jpg" \
  -F "study_type=chest_xray" \
  -F "patient_id=P123"
```

### Using httpie

```bash
# List all agents
http GET http://localhost:8000/agents

# Execute triage assessment
http POST http://localhost:8000/agents/triage/assess \
  chief_complaint="Chest pain" \
  symptoms:='["chest pain"]' \
  vitals:='{"heart_rate": 110}'

# Check drug interactions
http POST http://localhost:8000/agents/pharmacy/check \
  drug_names:='["warfarin", "aspirin"]' \
  patient_id="P123"
```

### Using Python requests

```python
import requests

# List all agents
response = requests.get("http://localhost:8000/agents")
agents = response.json()

# Execute triage assessment
response = requests.post(
    "http://localhost:8000/agents/triage/assess",
    json={
        "chief_complaint": "Chest pain",
        "symptoms": ["chest pain", "dyspnea"],
        "vitals": {"heart_rate": 110, "bp": "140/90"}
    }
)
result = response.json()

# Stream chat response
response = requests.post(
    "http://localhost:8000/agents/diagnostic/chat",
    json={"message": "What causes chest pain?"},
    stream=True
)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
