/**
 * MedAssist AI API Client
 *
 * Provides methods to interact with the backend REST API endpoints.
 * Handles fetching agents, triage queue, radiology reports, vitals,
 * and streaming chat responses via SSE.
 */

// API base URL - configurable via environment variable
export const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ||
                            process.env.REACT_APP_API_BASE_URL ||
                            "http://localhost:8000";

/**
 * Generic fetch wrapper with error handling
 */
async function fetchJSON(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      throw new Error("Backend is unreachable. Please ensure the server is running at " + API_BASE_URL);
    }
    throw error;
  }
}

/**
 * Agent API Methods
 */

/**
 * Fetch all registered agents
 * @returns {Promise<Array>} Array of agent objects with id, name, status, skills, queue, etc.
 */
export async function getAgents() {
  return fetchJSON("/agents");
}

/**
 * Fetch a specific agent by ID
 * @param {string} agentId - Agent identifier (e.g., "triage", "radiology")
 * @returns {Promise<Object>} Agent object
 */
export async function getAgent(agentId) {
  return fetchJSON(`/agents/${agentId}`);
}

/**
 * Execute a skill on an agent
 * @param {string} agentId - Agent identifier
 * @param {string} skillName - Skill name to execute
 * @param {Object} params - Skill parameters
 * @returns {Promise<Object>} Skill execution result
 */
export async function executeSkill(agentId, skillName, params) {
  return fetchJSON(`/agents/${agentId}/execute`, {
    method: "POST",
    body: JSON.stringify({ skill_name: skillName, params }),
  });
}

/**
 * Stream chat messages with an agent using Server-Sent Events (SSE)
 * @param {string} agentId - Agent identifier
 * @param {string} message - User message
 * @param {Object} context - Optional context object
 * @param {Function} onChunk - Callback for each streamed chunk
 * @param {Function} onError - Error callback
 * @returns {Promise<void>}
 */
export async function chatWithAgent(agentId, message, context = {}, onChunk, onError) {
  const url = `${API_BASE_URL}/agents/${agentId}/chat`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, context }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Parse SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6); // Remove "data: " prefix
          if (data.trim()) {
            onChunk(data);
          }
        }
      }
    }
  } catch (error) {
    if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      onError(new Error("Backend is unreachable. Please ensure the server is running."));
    } else {
      onError(error);
    }
  }
}

/**
 * Domain-Specific API Methods
 */

/**
 * Get triage patient queue
 * @returns {Promise<Array>} Array of patients in triage queue
 */
export async function getTriageQueue() {
  return fetchJSON("/agents/triage/queue");
}

/**
 * Submit patient for triage assessment
 * @param {Object} data - Triage assessment data (chief_complaint, symptoms, vitals, etc.)
 * @returns {Promise<Object>} Triage assessment result
 */
export async function assessTriage(data) {
  return fetchJSON("/agents/triage/assess", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Get latest radiology report
 * @returns {Promise<Object>} Latest radiology report
 */
export async function getLatestRadiologyReport() {
  return fetchJSON("/agents/radiology/reports/latest");
}

/**
 * Submit image for radiology analysis
 * @param {File} file - Image file
 * @param {string} studyType - Type of study (default: "chest_xray")
 * @param {string} patientId - Optional patient identifier
 * @returns {Promise<Object>} Analysis result
 */
export async function analyzeRadiologyImage(file, studyType = "chest_xray", patientId = null) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("study_type", studyType);
  if (patientId) {
    formData.append("patient_id", patientId);
  }

  const url = `${API_BASE_URL}/agents/radiology/analyze`;

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error.message.includes("Failed to fetch")) {
      throw new Error("Backend is unreachable");
    }
    throw error;
  }
}

/**
 * Get latest patient vitals
 * @returns {Promise<Object>} Latest vital signs
 */
export async function getLatestVitals() {
  return fetchJSON("/agents/monitoring/vitals/latest");
}

/**
 * Submit vitals for monitoring and MEWS score calculation
 * @param {Object} vitals - Vital signs data
 * @returns {Promise<Object>} Monitoring result with MEWS score
 */
export async function submitVitals(vitals) {
  return fetchJSON("/agents/monitoring/vitals", {
    method: "POST",
    body: JSON.stringify(vitals),
  });
}

/**
 * Check drug interactions
 * @param {Array<string>} drugNames - List of drug names
 * @param {string} patientId - Optional patient identifier
 * @param {Object} patientData - Optional patient data
 * @returns {Promise<Object>} Drug interaction result
 */
export async function checkDrugInteractions(drugNames, patientId = null, patientData = {}) {
  return fetchJSON("/agents/pharmacy/check", {
    method: "POST",
    body: JSON.stringify({
      drug_names: drugNames,
      patient_id: patientId,
      patient_data: patientData,
    }),
  });
}

/**
 * Generate clinical documentation
 * @param {Object} encounterData - Encounter data for SOAP note generation
 * @returns {Promise<Object>} Generated SOAP note
 */
export async function generateDocumentation(encounterData) {
  return fetchJSON("/agents/documentation/generate", {
    method: "POST",
    body: JSON.stringify({ encounter_data: encounterData }),
  });
}

/**
 * Search clinical evidence
 * @param {string} query - Search query
 * @returns {Promise<Object>} Research results
 */
export async function searchResearch(query) {
  return fetchJSON("/agents/research/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

/**
 * Generate UI component from prompt
 * @param {string} prompt - Natural language UI description
 * @returns {Promise<Object>} Generated component specification
 */
export async function generateUI(prompt) {
  return fetchJSON("/agents/genui/generate", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

/**
 * Get GenUI agent status
 * @returns {Promise<Object>} GenUI status and capabilities
 */
export async function getGenUIStatus() {
  return fetchJSON("/agents/genui/status");
}

/**
 * Generate a PowerPoint presentation from a natural language prompt.
 *
 * Calls the GenUI agent's ppt_generation skill via the 6-phase backend pipeline
 * (intent parse → content plan → pptxgenjs codegen → node execution → QA → delivery).
 * Generation typically takes 30-120 seconds; no timeout is set on the client side.
 *
 * @param {string} prompt - Natural language description of the desired presentation
 * @returns {Promise<{
 *   success: boolean,
 *   job_id: string,
 *   topic: string,
 *   slide_count: number,
 *   download_url: string,
 *   thumbnail_urls: string[],
 *   qa_performed: boolean,
 *   message: string
 * }>}
 * @throws {Error} On empty prompt, HTTP error, or network failure
 */
export async function generatePPT(prompt) {
  if (!prompt || !prompt.trim()) {
    throw new Error("Prompt is required to generate a presentation");
  }

  const url = `${API_BASE_URL}/agents/genui/ppt`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt.trim() }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `HTTP ${response.status}: PPT generation failed`);
    }

    return await response.json();
  } catch (error) {
    if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
      throw new Error(`Backend unreachable at ${API_BASE_URL}. Ensure the server is running.`);
    }
    throw error;
  }
}

/**
 * Build the absolute download URL for a generated .pptx file.
 *
 * @param {string} downloadUrl - Relative path returned by generatePPT() (e.g. "/agents/genui/ppt/download/<job_id>")
 * @returns {string|null} Absolute URL suitable for an <a href> download link
 */
export function getPPTDownloadURL(downloadUrl) {
  if (!downloadUrl) return null;
  return `${API_BASE_URL}${downloadUrl}`;
}

/**
 * Build the absolute URL for a slide thumbnail image.
 *
 * @param {string} thumbnailUrl - Relative path from thumbnail_urls[] (e.g. "/agents/genui/ppt/thumbnail/<job_id>/1")
 * @returns {string|null} Absolute URL suitable for an <img src>
 */
export function getPPTThumbnailURL(thumbnailUrl) {
  if (!thumbnailUrl) return null;
  return `${API_BASE_URL}${thumbnailUrl}`;
}

/**
 * Health check endpoint
 * @returns {Promise<Object>} Health status
 */
export async function healthCheck() {
  return fetchJSON("/health");
}
