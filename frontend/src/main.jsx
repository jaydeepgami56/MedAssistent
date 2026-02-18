import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { TamboProvider } from '@tambo-ai/react'
import { ThemeProvider } from './theme.jsx'
import { tamboComponents } from './tambo/components.jsx'
import MedAssistDashboard from './components/MedAssistDashboard'

const tamboApiKey = import.meta.env.VITE_TAMBO_API_KEY || '';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <TamboProvider apiKey={tamboApiKey} components={tamboComponents}>
      <ThemeProvider>
        <MedAssistDashboard />
      </ThemeProvider>
    </TamboProvider>
  </StrictMode>,
)
