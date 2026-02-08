# MedAssist AI — Project Structure & Setup Guide

Quick start guide and complete project file structure.

---

## Project Structure

```
medassist-ai/
├── config/
│   └── openclaw.json                  # OpenClaw config (LLM providers, gateway)
│
├── skills/                            # SKILL.md files for each agent
│   ├── triage/
│   │   ├── SKILL.md                   # Triage assessment skill
│   │   └── skill.json                 # {"name":"triage","version":"1.0"}
│   ├── radiology/
│   │   ├── SKILL.md                   # Medical image analysis skill
│   │   └── skill.json
│   ├── diagnostic/
│   │   ├── SKILL.md                   # Differential diagnosis skill
│   │   └── skill.json
│   ├── pharmacy/
│   │   ├── SKILL.md                   # Drug interaction check skill
│   │   └── skill.json
│   ├── monitoring/
│   │   ├── SKILL.md                   # Vital sign monitoring skill
│   │   └── skill.json
│   ├── documentation/
│   │   ├── SKILL.md                   # Clinical documentation skill
│   │   └── skill.json
│   └── research/
│       ├── SKILL.md                   # Evidence & research skill
│       └── skill.json
│
├── a2ui/                              # A2UI JSONL templates
│   ├── templates/
│   │   ├── triage-dashboard.jsonl     # Triage queue interface
│   │   ├── radiology-report.jsonl     # Radiology findings report
│   │   ├── drug-alert.jsonl           # Drug interaction alert
│   │   ├── patient-vitals.jsonl       # Real-time vitals monitor
│   │   ├── clinical-notes.jsonl       # SOAP note editor
│   │   └── evidence-panel.jsonl       # Research results display
│   └── components/
│       └── medical-components.md      # Custom component reference
│
├── backend/                           # Python FastAPI backend
│   ├── main.py                        # FastAPI application entry
│   ├── config.py                      # Environment & model config
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Base agent class
│   │   ├── triage_agent.py            # Triage agent implementation
│   │   ├── radiology_agent.py         # Radiology agent implementation
│   │   ├── diagnostic_agent.py        # Diagnostic agent implementation
│   │   ├── pharmacy_agent.py          # Pharmacy agent implementation
│   │   ├── monitoring_agent.py        # Monitoring agent implementation
│   │   ├── documentation_agent.py     # Documentation agent implementation
│   │   ├── research_agent.py          # Research agent implementation
│   │   └── coordinator_agent.py       # Coordinator/orchestrator agent
│   ├── models/
│   │   ├── __init__.py
│   │   ├── medimageinsight.py         # MedImageInsight wrapper
│   │   ├── medgemma.py                # MedGemma 4B/27B wrapper
│   │   ├── medsiglib.py               # MedSigLIP wrapper
│   │   └── clinical_bert.py           # ClinicalBERT NER wrapper
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── fhir_client.py             # FHIR R4 EHR integration
│   │   ├── rxnorm_client.py           # RxNorm drug database
│   │   ├── drugbank_client.py         # DrugBank interactions
│   │   ├── dicom_client.py            # Orthanc DICOM server
│   │   ├── pubmed_client.py           # PubMed literature search
│   │   └── qdrant_client.py           # Vector search client
│   └── requirements.txt
│
├── infrastructure/
│   ├── docker-compose.yml             # Local development stack
│   ├── Dockerfile                     # Application container
│   ├── Dockerfile.models              # Model serving container
│   └── k8s/
│       ├── namespace.yaml
│       ├── deployment-api.yaml        # FastAPI deployment
│       ├── deployment-models.yaml     # Model server deployment
│       ├── deployment-qdrant.yaml     # Qdrant vector DB
│       ├── deployment-orthanc.yaml    # DICOM server
│       ├── service.yaml               # Service definitions
│       ├── ingress.yaml               # Traefik ingress rules
│       └── argocd-app.yaml            # ArgoCD application
│
├── docs/
│   ├── 01-MedAssist-AI-Architecture.md
│   ├── 02-A2UI-Templates.md
│   ├── 03-SKILL-Files.md
│   └── 04-Project-Setup.md           # This file
│
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- Node.js ≥ 22
- Python ≥ 3.10
- Docker & Docker Compose
- kubectl + access to your Kubernetes cluster
- Anthropic API key (Claude)

### Step 1: Install OpenClaw

```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

### Step 2: Configure LLM Provider

Edit `~/.openclaw/openclaw.json`:

```json
{
  "models": {
    "default": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "apiKey": "YOUR_ANTHROPIC_API_KEY"
    },
    "local": {
      "provider": "openai-compatible",
      "baseUrl": "http://127.0.0.1:1234/v1",
      "model": "your-lm-studio-model",
      "contextWindow": 32768
    }
  }
}
```

### Step 3: Clone & Install

```bash
git clone <your-repo>/medassist-ai.git
cd medassist-ai

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Copy skills to OpenClaw workspace
cp -r ../skills/* ~/.openclaw/workspace/skills/
```

### Step 4: Deploy MedImageInsight

```bash
# Option A: HuggingFace (simplified)
git clone https://huggingface.co/lion-ai/MedImageInsights
cd MedImageInsights && uv sync

# Option B: Azure AI Foundry (official)
# Follow: https://ai.azure.com/catalog/models/MedImageInsight
```

### Step 5: Start Infrastructure

```bash
# Local development
docker-compose up -d

# OR Kubernetes
kubectl apply -f infrastructure/k8s/
```

### Step 6: Start Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 7: Push A2UI Templates

```bash
# Get your node ID
openclaw nodes list

# Push triage dashboard
openclaw nodes canvas a2ui push --jsonl a2ui/templates/triage-dashboard.jsonl --node <node-id>

# Push radiology report template
openclaw nodes canvas a2ui push --jsonl a2ui/templates/radiology-report.jsonl --node <node-id>
```

### Step 8: Verify

```bash
openclaw doctor
openclaw health
openclaw skills list
```

---

## Environment Variables

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514

# MedImageInsight
MEDIMAGEINSIGHT_MODEL_DIR=./models/medimageinsight

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Orthanc DICOM
ORTHANC_HOST=localhost
ORTHANC_PORT=8042

# FHIR
FHIR_BASE_URL=https://your-ehr.example.com/fhir

# RxNorm
RXNORM_API_URL=https://rxnav.nlm.nih.gov/REST

# DrugBank (if using API)
DRUGBANK_API_KEY=your-key

# PubMed
PUBMED_API_KEY=your-ncbi-key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_DB=medassist
POSTGRES_USER=medassist
POSTGRES_PASSWORD=your-password

# Security
ENCRYPTION_KEY=your-aes-256-key
```

---

## Docker Compose (Local Dev)

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, qdrant, orthanc]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: medassist
      POSTGRES_PASSWORD: dev-password
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: [qdrant_data:/qdrant/storage]

  orthanc:
    image: orthancteam/orthanc:latest
    ports: ["8042:8042", "4242:4242"]
    volumes: [orthanc_data:/var/lib/orthanc/db]

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/dev-password
    ports: ["7474:7474", "7687:7687"]
    volumes: [neo4j_data:/data]

volumes:
  pgdata:
  qdrant_data:
  orthanc_data:
  neo4j_data:
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | GET | List all agents with status and skills |
| `/agents/{id}` | GET | Get single agent details |
| `/agents/{id}/chat` | POST | Send message to agent (streaming) |
| `/agents/{id}/execute` | POST | Execute a specific skill with parameters |
| `/skills` | GET | List all registered skills |
| `/triage/assess` | POST | Submit patient for triage assessment |
| `/radiology/analyze` | POST | Submit image for radiology analysis |
| `/pharmacy/check` | POST | Check drug interactions |
| `/monitoring/vitals` | POST | Submit vital signs |
| `/documentation/generate` | POST | Generate clinical note |
| `/research/search` | POST | Search clinical evidence |
| `/health` | GET | System health check |
