import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import MedAssistDashboard from './components/MedAssistDashboard'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MedAssistDashboard />
  </StrictMode>,
)
