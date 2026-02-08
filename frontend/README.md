# MedAssist AI Frontend

React-based dashboard UI for MedAssist AI v2.0 multi-agent medical platform.

## Features

- **Agent Control Center**: View and interact with 8 specialized medical AI agents
- **Triage Dashboard**: ESI scoring, patient queue, red flag detection
- **Radiology Analysis**: Image analysis reports with confidence scores and KNN evidence
- **Vitals Monitor**: Real-time vital signs tracking with MEWS scoring
- **Agent Chat**: Stream conversations with individual agents using SSE

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Vanilla CSS-in-JS** - Inline styles (no dependencies)

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

### API Base URL

Set the backend API URL via environment variable:

```bash
# Create .env file
cp .env.example .env

# Edit VITE_API_BASE_URL
# Default: http://localhost:8000
```

### Development Proxy

Vite dev server proxies `/agents` and `/health` requests to `http://localhost:8000` by default. Configure in `vite.config.js` if needed.

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   └── MedAssistDashboard.jsx  # Main dashboard component
│   ├── services/
│   │   └── api.js                   # Backend API client
│   └── main.jsx                     # App entry point
├── index.html                        # HTML template
├── vite.config.js                    # Vite configuration
└── package.json                      # Dependencies
```

## API Integration

All API calls go through `src/services/api.js`:

- `getAgents()` - Fetch all agents
- `getTriageQueue()` - Fetch triage patient queue
- `getLatestRadiologyReport()` - Fetch latest radiology report
- `getLatestVitals()` - Fetch latest vital signs
- `chatWithAgent(agentId, message, context, onChunk, onError)` - Stream chat with SSE

## Error Handling

- **Backend Unreachable**: Red error banner shown at top of UI
- **Failed Requests**: Error state displayed in affected views
- **Chat Errors**: Error message displayed in chat conversation

## Backend Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agents` | GET | List all agents |
| `/agents/{id}` | GET | Get single agent |
| `/agents/{id}/chat` | POST | Stream chat (SSE) |
| `/agents/{id}/execute` | POST | Execute skill |
| `/agents/triage/queue` | GET | Get triage patient queue |
| `/agents/triage/assess` | POST | Submit for triage assessment |
| `/agents/radiology/reports/latest` | GET | Get latest radiology report |
| `/agents/radiology/analyze` | POST | Upload image for analysis |
| `/agents/monitoring/vitals/latest` | GET | Get latest vitals |
| `/agents/monitoring/vitals` | POST | Submit vitals for MEWS score |
| `/agents/pharmacy/check` | POST | Check drug interactions |
| `/agents/documentation/generate` | POST | Generate SOAP notes |
| `/agents/research/search` | POST | Search clinical evidence |

## Development

### Hot Reload

Vite dev server supports hot module replacement. Save any file and changes appear instantly.

### CORS

If running frontend and backend on different ports, ensure backend has CORS configured:

```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

```bash
# Build production bundle
npm run build

# Output: dist/ directory

# Serve with any static file server
npx serve dist

# Or deploy to:
# - Vercel: vercel deploy
# - Netlify: netlify deploy
# - Azure Static Web Apps
# - AWS S3 + CloudFront
```

Set `VITE_API_BASE_URL` to production backend URL before building.

## License

Part of the OpenClaw MedAssist AI project.
