# MedAssist AI Platform

A comprehensive medical multi-agent platform built on **OpenClaw** with **A2UI** (Agent-to-User Interface) for intelligent healthcare assistance. MedAssist orchestrates 8 specialized AI agents for imaging, triage, clinical decision support, drug interaction, monitoring, documentation, and research—all through a unified, secure, and visually rich interface.

---

## Features

- **8 Medical AI Agents**: Triage, Radiology, Diagnostic, Pharmacy, Monitoring, Documentation, Research, Coordinator
- **A2UI Templates**: JSONL-based UI for clinical workflows
- **Multi-Agent Consensus**: For complex medical cases
- **Real-Time Monitoring**: Vitals, alerts, and early warning
- **Automated Documentation**: SOAP notes, discharge summaries
- **Evidence-Based Research**: PubMed, guidelines, trial matching

---

## Project Structure

```
openclaw/
├── backend/           # FastAPI backend (Python)
├── frontend/          # React dashboard (Vite)
├── a2ui/              # A2UI JSONL templates
├── skills/            # SKILL.md files for each agent
├── config/            # Configuration files
├── infrastructure/    # Docker Compose, deployment
├── docs/              # Architecture, setup, and guides
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for local stack)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Local Development Stack
```bash
cd infrastructure
docker-compose up -d
```
Services: PostgreSQL, Qdrant, Orthanc (DICOM), Neo4j

---

## Configuration
- Copy `.env.example` to `.env` in both `backend/` and `frontend/`.
- Edit API keys and service URLs as needed.

---

## Documentation
- [docs/01-MedAssist-AI-Architecture.md](docs/01-MedAssist-AI-Architecture.md): System architecture, agent design
- [docs/04-Project-Setup.md](docs/04-Project-Setup.md): Setup and file structure
- [frontend/README.md](frontend/README.md): Frontend usage and API integration

---

## License
MIT License
