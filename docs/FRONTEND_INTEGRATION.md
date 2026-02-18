# Frontend-Backend Integration Guide

This document describes how the MedAssist AI frontend integrates with the backend API.

## Overview

The React dashboard (`frontend/src/components/MedAssistDashboard.jsx`) connects to the FastAPI backend (`backend/`) to provide real-time data for:

- **Agent Management**: List and interact with 8 specialist agents
- **Triage Queue**: Live patient queue with ESI scoring
- **Radiology Reports**: Latest imaging analysis results
- **Vitals Monitoring**: Real-time vital signs and MEWS scoring
- **Agent Chat**: Streaming conversations using Server-Sent Events (SSE)

## Quick Start

### 1. Start Backend Server

```bash
cd C:/Dev/openclaw
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn backend.main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start Frontend Dev Server

```bash
npm run dev
```

Frontend runs at: **http://localhost:3000**

### 4. Open Browser

Navigate to: **http://localhost:3000**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (localhost:3000)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  MedAssistDashboard.jsx                                │    │
│  │  - useState/useEffect hooks                            │    │
│  │  - View routing (dashboard/triage/radiology/vitals)   │    │
│  │  - Error handling and loading states                  │    │
│  └─────────────────┬──────────────────────────────────────┘    │
│                    │                                             │
│  ┌─────────────────▼──────────────────────────────────────┐    │
│  │  api.js (Service Layer)                                │    │
│  │  - getAgents(), getTriageQueue(), etc.                 │    │
│  │  - SSE streaming for chat                              │    │
│  │  - Error handling (unreachable backend)                │    │
│  └─────────────────┬──────────────────────────────────────┘    │
└────────────────────┼──────────────────────────────────────────┘
                     │ HTTP/SSE
                     │
┌────────────────────▼──────────────────────────────────────────┐
│              FastAPI Backend (localhost:8000)                  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  routers/agents.py                                     │   │
│  │  - GET /agents                                         │   │
│  │  - GET /agents/{id}                                    │   │
│  │  - POST /agents/{id}/chat (SSE streaming)             │   │
│  │  - POST /agents/{id}/execute                           │   │
│  │  - GET /agents/triage/queue                            │   │
│  │  - GET /agents/radiology/reports/latest                │   │
│  │  - GET /agents/monitoring/vitals/latest                │   │
│  │  + Domain-specific POST endpoints                      │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
│  ┌─────────────────▼──────────────────────────────────────┐   │
│  │  Agent Layer (8 specialist agents)                     │   │
│  │  - Triage, Radiology, Diagnostic, Pharmacy, etc.       │   │
│  │  - Claude API / MedGemma / MedImageInsight             │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Core Agent Endpoints

| Endpoint | Method | Frontend Usage |
|----------|--------|----------------|
| `/agents` | GET | Dashboard: Fetch all agents on mount |
| `/agents/{id}` | GET | (Not currently used) |
| `/agents/{id}/chat` | POST | Agent Chat: Stream SSE responses |
| `/agents/{id}/execute` | POST | (Not currently used directly) |

### Queue/Data Endpoints (New in US-028)

| Endpoint | Method | Frontend Usage |
|----------|--------|----------------|
| `/agents/triage/queue` | GET | Triage View: Fetch patient queue |
| `/agents/radiology/reports/latest` | GET | Radiology View: Fetch latest report |
| `/agents/monitoring/vitals/latest` | GET | Vitals View: Fetch latest vital signs |

### Domain-Specific POST Endpoints

| Endpoint | Method | Frontend Usage |
|----------|--------|----------------|
| `/agents/triage/assess` | POST | Submit patient for triage (future) |
| `/agents/radiology/analyze` | POST | Upload image for analysis (future) |
| `/agents/monitoring/vitals` | POST | Submit vitals for MEWS calculation (future) |
| `/agents/pharmacy/check` | POST | Check drug interactions (future) |
| `/agents/documentation/generate` | POST | Generate SOAP notes (future) |
| `/agents/research/search` | POST | Search clinical evidence (future) |

## Data Flow Examples

### 1. Dashboard - Fetch Agents

```javascript
// frontend/src/components/MedAssistDashboard.jsx
useEffect(() => {
  async function fetchAgents() {
    const agentsData = await api.getAgents();
    setAgents(agentsData);
  }
  fetchAgents();
}, []);
```

**Backend:**
```python
# backend/routers/agents.py
@router.get("")
async def list_agents():
    agents = get_all_agents()
    return [agent.get_info() for agent in agents]
```

**Response:**
```json
[
  {
    "agent_id": "triage",
    "name": "Triage Agent",
    "status": "Active",
    "skills": ["ESI Scoring", "Red Flag Detection", ...],
    "queue": 12,
    "models_used": ["ClinicalBERT", "Claude API"],
    "color": "#ef4444",
    "icon": "🚨"
  },
  ...
]
```

### 2. Triage View - Fetch Queue

```javascript
useEffect(() => {
  if (activeView === "triage") {
    const queue = await api.getTriageQueue();
    setTriagePatients(queue);
  }
}, [activeView]);
```

**Backend:**
```python
@router.get("/triage/queue")
async def get_triage_queue():
    # Returns mock data (replace with DB query in production)
    return [{"id": 1, "name": "Patient A", "esi": 1, ...}, ...]
```

### 3. Agent Chat - SSE Streaming

```javascript
await api.chatWithAgent(
  agentId,
  userMessage,
  {},
  (chunk) => {
    // Update UI with each streamed chunk
    fullResponse += chunk;
    setChatMessages(prev => [...prev.slice(0, -1), { text: fullResponse }]);
  },
  (error) => {
    console.error("Chat error:", error);
  }
);
```

**Backend:**
```python
@router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: str, request: ChatRequest):
    async def generate():
        async for chunk in agent.chat(request.message, request.context):
            yield f"data: {chunk}\n\n"  # SSE format
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**SSE Stream:**
```
data: Hello

data: !

data:  I'm

data:  the

data:  Triage

data:  Agent

data: ...
```

## Error Handling

### Backend Unreachable

When `fetch()` fails (e.g., backend not running):

```javascript
// api.js
catch (error) {
  if (error.message.includes("Failed to fetch")) {
    throw new Error("Backend is unreachable. Please ensure the server is running at " + API_BASE_URL);
  }
}
```

**UI Response:**
- Red error banner at top: "⚠️ Backend is unreachable..."
- Status indicator in NavBar turns red
- Loading states show "Backend Error"

### HTTP Errors

When backend returns non-200 status:

```javascript
if (!response.ok) {
  const error = await response.json().catch(() => ({ detail: response.statusText }));
  throw new Error(error.detail || `HTTP ${response.status}`);
}
```

**UI Response:**
- Error banner shows specific error message from backend
- Affected view shows error state instead of data

## Configuration

### API Base URL

Frontend connects to backend via configurable base URL:

```javascript
// frontend/src/services/api.js
export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ||
                            process.env.REACT_APP_API_BASE_URL ||
                            "http://localhost:8000";
```

**Development:** Use `.env` file:
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

**Production:** Set environment variable before build:
```bash
export VITE_API_BASE_URL=https://api.medassist.example.com
npm run build
```

### CORS Configuration

Backend must allow frontend origin:

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.medassist.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development Workflow

### Adding a New View

1. **Add Backend Endpoint** (if needed):
   ```python
   # backend/routers/agents.py
   @router.get("/new-view/data")
   async def get_new_view_data():
       return {"data": "..."}
   ```

2. **Add API Method**:
   ```javascript
   // frontend/src/services/api.js
   export async function getNewViewData() {
     return fetchJSON("/agents/new-view/data");
   }
   ```

3. **Add UI State**:
   ```javascript
   // frontend/src/components/MedAssistDashboard.jsx
   const [newViewData, setNewViewData] = useState(null);
   ```

4. **Add useEffect Hook**:
   ```javascript
   useEffect(() => {
     if (activeView === "newview") {
       const data = await api.getNewViewData();
       setNewViewData(data);
     }
   }, [activeView]);
   ```

5. **Add View Component**:
   ```javascript
   const NewView = () => (
     <div style={{ padding: 20 }}>
       {/* Render newViewData */}
     </div>
   );
   ```

6. **Add to Router**:
   ```javascript
   {activeView === "newview" && <NewView />}
   ```

## Testing

### Manual Testing

1. **Start Backend**: `uvicorn backend.main:app --reload --port 8000`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Test Each View**:
   - Dashboard: Verify agents load from API
   - Triage: Verify queue loads from API
   - Radiology: Verify report loads from API
   - Vitals: Verify vitals load from API
   - Agent Chat: Send message, verify SSE streaming works

### Error Testing

1. **Backend Down**: Stop backend, verify error banner shows
2. **Invalid Data**: Modify backend to return invalid data, verify error handling

### API Testing

Use `curl` to test endpoints directly:

```bash
# List agents
curl http://localhost:8000/agents

# Get triage queue
curl http://localhost:8000/agents/triage/queue

# Chat with agent (SSE)
curl -N -X POST http://localhost:8000/agents/triage/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "context": {}}'
```

## Troubleshooting

### Frontend can't connect to backend

**Symptoms:** Error banner "Backend is unreachable"

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check API_BASE_URL is correct
3. Check CORS is configured on backend
4. Check firewall isn't blocking port 8000

### Agents not loading

**Symptoms:** Dashboard shows "Loading agents..." indefinitely

**Solutions:**
1. Check backend logs for errors
2. Verify all agents initialized in `backend/main.py` lifespan()
3. Check `/agents` endpoint: `curl http://localhost:8000/agents`

### Chat not streaming

**Symptoms:** Chat shows "[ERROR] ..." message

**Solutions:**
1. Verify agent exists and is initialized
2. Check Claude API key is configured: `backend/.env` has `ANTHROPIC_API_KEY`
3. Test endpoint directly: `curl -N -X POST http://localhost:8000/agents/triage/chat ...`

### Data not refreshing

**Symptoms:** Triage/radiology/vitals views show stale data

**Solutions:**
1. Views only fetch on mount/view change. Add refresh button if needed:
   ```javascript
   const handleRefresh = async () => {
     const queue = await api.getTriageQueue();
     setTriagePatients(queue);
   };
   ```
2. Or add auto-refresh with interval:
   ```javascript
   useEffect(() => {
     const interval = setInterval(async () => {
       const queue = await api.getTriageQueue();
       setTriagePatients(queue);
     }, 30000); // Refresh every 30s
     return () => clearInterval(interval);
   }, []);
   ```

## Next Steps

### Production Readiness

- [ ] Replace mock queue data with database queries
- [ ] Add authentication (OAuth2-Proxy + Azure AD)
- [ ] Add real-time updates (WebSockets or polling)
- [ ] Add refresh buttons / auto-refresh
- [ ] Add loading skeletons instead of "Loading..."
- [ ] Add pagination for large queues
- [ ] Add filtering/sorting for patient queues
- [ ] Add error retry logic (exponential backoff)
- [ ] Add analytics tracking
- [ ] Add accessibility (ARIA labels, keyboard nav)

### Performance Optimization

- [ ] Implement React.memo for expensive components
- [ ] Add request debouncing for search/filters
- [ ] Add lazy loading for agent chat history
- [ ] Add service worker for offline support
- [ ] Add bundle size optimization (code splitting)

### Testing

- [ ] Add unit tests (Vitest + React Testing Library)
- [ ] Add integration tests (Playwright)
- [ ] Add E2E tests for critical flows
- [ ] Add API contract tests
- [ ] Add accessibility tests (axe-core)

## Summary

The frontend integration is complete with:

✅ All agents fetch from `/agents` API on mount
✅ Triage view fetches queue from `/agents/triage/queue`
✅ Radiology view fetches report from `/agents/radiology/reports/latest`
✅ Vitals view fetches vitals from `/agents/monitoring/vitals/latest`
✅ Agent chat streams responses via SSE from `/agents/{id}/chat`
✅ Error handling for unreachable backend
✅ Configurable API base URL
✅ Existing UI design preserved

The system is now a fully integrated frontend-backend application ready for further development and production hardening.
