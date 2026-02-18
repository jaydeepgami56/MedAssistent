import { useState, useEffect, useCallback, useReducer, useRef } from "react";
import * as api from "../services/api";
import { useTheme } from "../theme.jsx";
import InputArea from "./InputArea.jsx";
import TamboPanel from "../tambo/TamboPanel.jsx";

const appFontStack = "'Inter', 'Space Grotesk', 'SF Pro Display', 'Segoe UI', sans-serif";
const headingFont = "'Space Grotesk', 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif";

// Chat messages reducer — defined outside component to avoid re-creation
const chatReducer = (state, action) => {
  switch (action.type) {
    case "SET": return action.payload;
    case "ADD": return [...state, action.payload];
    case "UPDATE_LAST": {
      const updated = [...state];
      updated[updated.length - 1] = action.payload;
      return updated;
    }
    case "CLEAR": return [];
    default: return state;
  }
};

// Shimmer keyframes injected once
const SHIMMER_STYLE_ID = "shimmer-keyframes";
if (typeof document !== "undefined" && !document.getElementById(SHIMMER_STYLE_ID)) {
  const style = document.createElement("style");
  style.id = SHIMMER_STYLE_ID;
  style.textContent = `@keyframes shimmer{0%{background-position:-400px 0}100%{background-position:400px 0}}`;
  document.head.appendChild(style);
}

function ShimmerBlock({ width = "100%", height = 14, radius = 6, style: extra = {} }) {
  return (
    <div style={{
      width, height, borderRadius: radius,
      background: "linear-gradient(90deg, var(--bg-tertiary) 25%, var(--border) 50%, var(--bg-tertiary) 75%)",
      backgroundSize: "800px 100%",
      animation: "shimmer 1.5s infinite linear",
      ...extra,
    }} />
  );
}

function SkeletonCard() {
  return (
    <div style={{
      padding: 20, borderRadius: 12,
      border: "1px solid var(--border)",
      background: "var(--card-bg)",
      maxWidth: "90%",
    }}>
      <ShimmerBlock width="45%" height={18} style={{ marginBottom: 10 }} />
      <ShimmerBlock width="70%" height={12} style={{ marginBottom: 16 }} />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <ShimmerBlock height={48} />
        <ShimmerBlock height={48} />
        <ShimmerBlock height={48} />
        <ShimmerBlock height={48} />
      </div>
      <ShimmerBlock width="30%" height={36} radius={8} style={{ marginTop: 16 }} />
    </div>
  );
}

// Helper: try to extract a JSON component spec from text (mirrors backend _extract_json)
function tryExtractComponentSpec(text) {
  if (!text || typeof text !== "string") return null;
  const trimmed = text.trim();
  // Try direct parse
  try {
    const obj = JSON.parse(trimmed);
    if (obj && obj.component_type) return obj;
  } catch {}
  // Try extracting from markdown code fences
  const fenceMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenceMatch) {
    try {
      const obj = JSON.parse(fenceMatch[1].trim());
      if (obj && obj.component_type) return obj;
    } catch {}
  }
  // Try finding first { ... } block
  const braceMatch = trimmed.match(/\{[\s\S]*\}/);
  if (braceMatch) {
    try {
      const obj = JSON.parse(braceMatch[0]);
      if (obj && obj.component_type) return obj;
    } catch {}
  }
  return null;
}

// Helper: generate a subtle tinted background from an accent color
function accentBg(hex, opacity = 0.07) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
}

export default function MedAssistDashboard() {
  const { theme, toggleTheme } = useTheme();

  // State management
  const [activeView, setActiveView] = useState("dashboard");
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatMessages, dispatchChatMessages] = useReducer(chatReducer, []);
  const [inputText, setInputText] = useState("");
  const textareaRef = useRef(null);

  // API data state
  const [agents, setAgents] = useState([]);
  const [triagePatients, setTriagePatients] = useState([]);
  const [radiologyReport, setRadiologyReport] = useState(null);
  const [vitals, setVitals] = useState(null);
  // Floating GenUI widget state
  const [genUIOpen, setGenUIOpen] = useState(false);
  const [genUIMessages, dispatchGenUI] = useReducer(chatReducer, [
    { role: "assistant", text: "Describe any UI component and I'll generate it for you. Try: \"patient vitals dashboard\" or \"appointment form\"." },
  ]);
  const [genUIInput, setGenUIInput] = useState("");
  const genUIChatRef = useRef(null);
  // Canvas state — auto-placed components
  const [canvasItems, setCanvasItems] = useState([]);
  const [editingItemId, setEditingItemId] = useState(null);

  // Error / loading state
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── Data fetching ─────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const agentsData = await api.getAgents();
        setAgents(agentsData.map(a => ({ ...a, id: a.agent_id })));
      } catch (err) {
        console.error("Failed to fetch agents:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (activeView === "triage") {
      (async () => {
        try { setError(null); setTriagePatients(await api.getTriageQueue()); }
        catch (err) { setError(err.message); }
      })();
    }
  }, [activeView]);

  useEffect(() => {
    if (activeView === "radiology") {
      (async () => {
        try { setError(null); setRadiologyReport(await api.getLatestRadiologyReport()); }
        catch (err) { setError(err.message); }
      })();
    }
  }, [activeView]);

  useEffect(() => {
    if (activeView === "vitals") {
      (async () => {
        try { setError(null); setVitals(await api.getLatestVitals()); }
        catch (err) { setError(err.message); }
      })();
    }
  }, [activeView]);

  // ── Handlers ──────────────────────────────────────────────────
  const handleAgentClick = (agent) => {
    setSelectedAgent(agent);
    setActiveView("agent");
    setInputText("");
    dispatchChatMessages({
      type: "SET",
      payload: [
        { role: "system", text: `${agent.name} activated. Ready to assist.` },
        { role: "assistant", text: `Hello! I'm the ${agent.name}. How can I help you today? My available skills are: ${agent.skills.join(", ")}.` },
      ],
    });
  };

  const handleSend = useCallback(async () => {
    if (!inputText.trim()) return;
    const userMessage = inputText;
    dispatchChatMessages({ type: "ADD", payload: { role: "user", text: userMessage } });
    setInputText("");
    dispatchChatMessages({ type: "ADD", payload: { role: "assistant", text: "", streaming: true } });

    try {
      let fullResponse = "";
      await api.chatWithAgent(
        selectedAgent.id,
        userMessage,
        {},
        (chunk) => {
          fullResponse += chunk;
          dispatchChatMessages({ type: "UPDATE_LAST", payload: { role: "assistant", text: fullResponse, streaming: true } });
        },
        (error) => {
          dispatchChatMessages({ type: "UPDATE_LAST", payload: { role: "assistant", text: `[ERROR] ${error.message}`, streaming: false } });
        }
      );
      dispatchChatMessages({ type: "UPDATE_LAST", payload: { role: "assistant", text: fullResponse } });
    } catch (err) {
      dispatchChatMessages({ type: "UPDATE_LAST", payload: { role: "assistant", text: `[ERROR] ${err.message}` } });
    }
  }, [selectedAgent?.id, inputText]);

  // ── Reusable style helpers ────────────────────────────────────
  const v = (name) => `var(${name})`;

  const cardStyle = {
    background: v("--card-bg"),
    borderRadius: 12,
    border: `1px solid ${v("--border")}`,
    boxShadow: v("--card-shadow"),
    transition: "box-shadow 0.2s, transform 0.2s",
  };

  // ── NavBar ────────────────────────────────────────────────────
  const NavBar = () => (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "10px 24px",
      background: v("--nav-bg"), borderBottom: `1px solid ${v("--nav-border")}`,
      fontFamily: appFontStack,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 24 }}>🏥</span>
        <span style={{ color: v("--brand-text"), fontWeight: 700, fontSize: 17, letterSpacing: 0.3, fontFamily: headingFont }}>MedAssist AI</span>
        <span style={{ color: v("--text-muted"), fontSize: 12, marginLeft: 2 }}>v2.0</span>
      </div>

      <div style={{ display: "flex", gap: 2 }}>
        {["dashboard", "triage", "radiology", "vitals", "canvas"].map(view => {
          const isActive = activeView === view;
          return (
            <button key={view}
              onClick={() => { setActiveView(view); setSelectedAgent(null); }}
              style={{
                padding: "6px 16px", borderRadius: 6,
                border: "none",
                background: isActive ? v("--active-nav-bg") : "transparent",
                color: isActive ? v("--brand-text") : v("--text-secondary"),
                fontSize: 13, fontWeight: isActive ? 600 : 400,
                cursor: "pointer", textTransform: "capitalize",
                fontFamily: appFontStack,
                borderBottom: isActive ? `2px solid ${v("--active-nav-border")}` : "2px solid transparent",
              }}>
              {view}
            </button>
          );
        })}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{
            width: 7, height: 7, borderRadius: "50%",
            background: error ? "#ef4444" : "#22c55e",
            boxShadow: error ? "0 0 4px #ef4444" : "0 0 4px #22c55e",
          }} />
          <span style={{ color: v("--text-muted"), fontSize: 11 }}>
            {loading ? "Loading..." : error ? "Error" : `${agents.filter(a => a.status === "Active").length} Online`}
          </span>
        </div>

        <button
          onClick={toggleTheme}
          title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          style={{
            padding: "6px 10px", borderRadius: 6,
            border: `1px solid ${v("--border")}`,
            background: v("--hover-bg"),
            color: v("--text-secondary"),
            fontSize: 16, cursor: "pointer", lineHeight: 1,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
          {theme === "light" ? "🌙" : "☀️"}
        </button>
      </div>
    </div>
  );

  // ── Error Banner ──────────────────────────────────────────────
  const ErrorBanner = () => error && (
    <div style={{
      padding: "10px 24px",
      background: v("--error-bg"), borderBottom: `1px solid ${v("--error-border")}`,
      display: "flex", alignItems: "center", gap: 8,
    }}>
      <span style={{ color: "#ef4444", fontSize: 13 }}>⚠️</span>
      <span style={{ color: "#ef4444", fontSize: 12 }}>{error}</span>
      <button onClick={() => setError(null)}
        style={{ marginLeft: "auto", background: "transparent", border: "none", color: v("--text-muted"), cursor: "pointer", fontSize: 16 }}>
        ×
      </button>
    </div>
  );

  // ── Dashboard View ────────────────────────────────────────────
  const Dashboard = () => {
    if (loading) {
      return <div style={{ padding: 40, textAlign: "center", color: v("--text-muted"), fontSize: 14 }}>Loading agents...</div>;
    }

    const activeAgents = agents.filter(a => a.status === "Active").length;
    const totalQueue = agents.reduce((sum, a) => sum + (a.queue || 0), 0);

    return (
      <div style={{ padding: "32px 36px", fontFamily: appFontStack }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 28 }}>
          <div>
            <h2 style={{ color: v("--text-primary"), margin: 0, fontSize: 24, fontWeight: 700, fontFamily: headingFont }}>Agent Control Center</h2>
            <p style={{ color: v("--text-muted"), margin: "6px 0 0", fontSize: 14 }}>
              {agents.length} specialized medical agents powered by OpenClaw
            </p>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            {[
              { label: "Active", val: `${activeAgents}/${agents.length}`, color: "#22c55e" },
              { label: "Queue", val: totalQueue.toString(), color: "#f59e0b" },
              { label: "ESI-1", val: (triagePatients.filter(p => p.esi === 1).length || 0).toString(), color: "#ef4444" },
            ].map(s => (
              <div key={s.label} style={{
                textAlign: "center", padding: "10px 18px",
                ...cardStyle, borderLeft: `3px solid ${s.color}`,
              }}>
                <div style={{ color: s.color, fontSize: 22, fontWeight: 700 }}>{s.val}</div>
                <div style={{ color: v("--text-muted"), fontSize: 11, marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
          {agents.map(a => (
            <div key={a.id} onClick={() => handleAgentClick(a)}
              style={{
                ...cardStyle,
                padding: 18, cursor: "pointer",
                borderLeft: `3px solid ${a.color}`,
              }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = "var(--card-hover-shadow)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = "var(--card-shadow)"; e.currentTarget.style.transform = "translateY(0)"; }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 28 }}>{a.icon}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: a.status === "Active" ? "#22c55e" : v("--text-muted") }} />
                  <span style={{ color: a.status === "Active" ? "#22c55e" : v("--text-muted"), fontSize: 10, fontWeight: 500 }}>{a.status}</span>
                </div>
              </div>
              <div style={{ color: a.color, fontWeight: 600, fontSize: 15, marginBottom: 8, fontFamily: headingFont }}>{a.name}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
                {a.skills.slice(0, 3).map(s => (
                  <span key={s} style={{
                    padding: "3px 8px", borderRadius: 4,
                    background: accentBg(a.color, 0.08),
                    color: a.color, fontSize: 10, fontWeight: 500,
                  }}>{s}</span>
                ))}
              </div>
              {a.queue > 0 && (
                <div style={{ color: v("--text-muted"), fontSize: 11 }}>Queue: <span style={{ color: a.color, fontWeight: 600 }}>{a.queue}</span></div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ── Triage View ───────────────────────────────────────────────
  const TriageView = () => (
    <div style={{ padding: "32px 36px", fontFamily: appFontStack }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ color: "#ef4444", margin: 0, fontSize: 24, fontWeight: 700, fontFamily: headingFont }}>🚨 Triage Dashboard</h2>
        <div style={{ display: "flex", gap: 6 }}>
          {[
            { esi: "ESI-1", count: triagePatients.filter(p => p.esi === 1).length, color: "#ef4444" },
            { esi: "ESI-2", count: triagePatients.filter(p => p.esi === 2).length, color: "#f97316" },
            { esi: "ESI-3", count: triagePatients.filter(p => p.esi === 3).length, color: "#eab308" },
            { esi: "ESI-4", count: triagePatients.filter(p => p.esi === 4).length, color: "#22c55e" },
            { esi: "ESI-5", count: triagePatients.filter(p => p.esi === 5).length, color: "#3b82f6" },
          ].map(e => (
            <div key={e.esi} style={{
              padding: "5px 12px", borderRadius: 6,
              background: accentBg(e.color, 0.08), border: `1px solid ${accentBg(e.color, 0.2)}`,
              textAlign: "center",
            }}>
              <div style={{ color: e.color, fontSize: 15, fontWeight: 700 }}>{e.count}</div>
              <div style={{ color: v("--text-muted"), fontSize: 9 }}>{e.esi}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {triagePatients.map(p => (
          <div key={p.id} style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "11px 16px",
            ...cardStyle, borderLeft: `4px solid ${p.color}`,
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%",
              background: accentBg(p.color, 0.12),
              display: "flex", alignItems: "center", justifyContent: "center",
              color: p.color, fontWeight: 700, fontSize: 13, flexShrink: 0,
            }}>{p.esi}</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: v("--text-primary"), fontSize: 13, fontWeight: 600 }}>{p.name}</span>
                <span style={{ color: p.color, fontSize: 10, padding: "2px 8px", borderRadius: 10, background: accentBg(p.color, 0.1) }}>{p.label}</span>
              </div>
              <div style={{ color: v("--text-secondary"), fontSize: 11, marginTop: 2 }}>{p.complaint}</div>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <div style={{ color: v("--text-muted"), fontSize: 10 }}>Wait</div>
              <div style={{ color: p.color, fontSize: 12, fontWeight: 600 }}>{p.time}</div>
            </div>
            <button style={{
              padding: "5px 12px", borderRadius: 5,
              border: `1px solid ${accentBg(p.color, 0.3)}`,
              background: "transparent", color: p.color, fontSize: 10, cursor: "pointer",
            }}>View</button>
          </div>
        ))}
      </div>

      <div style={{
        marginTop: 12, padding: 10, borderRadius: 6,
        background: v("--error-bg"), border: `1px solid ${v("--error-border")}`,
      }}>
        <div style={{ color: "#ef4444", fontSize: 10, fontWeight: 600, marginBottom: 3 }}>⚠️ AI-ASSISTED TRIAGE — REQUIRES CLINICIAN VERIFICATION</div>
        <div style={{ color: v("--text-muted"), fontSize: 9 }}>ESI scores are generated by ClinicalBERT + Claude API. ESI 1-2 cases auto-escalate to attending physician.</div>
      </div>
    </div>
  );

  // ── Radiology View ────────────────────────────────────────────
  const RadiologyView = () => {
    if (!radiologyReport) {
      return <div style={{ padding: 40, textAlign: "center", color: v("--text-muted"), fontSize: 14 }}>Loading radiology report...</div>;
    }

    return (
      <div style={{ padding: "32px 36px", fontFamily: appFontStack }}>
        <h2 style={{ color: "#00b4d8", margin: "0 0 20px", fontSize: 24, fontWeight: 700, fontFamily: headingFont }}>🩻 Radiology Analysis Report</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div>
            <div style={{ ...cardStyle, padding: 16, marginBottom: 12 }}>
              <div style={{ color: v("--text-muted"), fontSize: 10, marginBottom: 6 }}>PATIENT INFO</div>
              <div style={{ color: v("--text-primary"), fontSize: 14, fontWeight: 600 }}>{radiologyReport.patient}</div>
              <div style={{ color: v("--text-secondary"), fontSize: 11, marginTop: 2 }}>Modality: {radiologyReport.modality}</div>
              <div style={{ color: v("--text-muted"), fontSize: 10, marginTop: 4 }}>Model: MedImageInsight + MedGemma 4B</div>
            </div>
            <div style={{ ...cardStyle, padding: 16 }}>
              <div style={{ color: "#00b4d8", fontSize: 12, fontWeight: 600, marginBottom: 10 }}>Findings</div>
              {radiologyReport.findings.map((f, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "8px 0",
                  borderBottom: i < radiologyReport.findings.length - 1 ? `1px solid ${v("--border")}` : "none",
                }}>
                  <div style={{
                    width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
                    background: f.severity === "high" ? "#ef4444" : f.severity === "moderate" ? "#f59e0b" : "#22c55e",
                  }} />
                  <div style={{ flex: 1, color: v("--text-primary"), fontSize: 11 }}>{f.text}</div>
                  <div style={{
                    padding: "2px 8px", borderRadius: 10, fontSize: 10,
                    background: accentBg(f.confidence > 0.9 ? "#22c55e" : "#f59e0b", 0.1),
                    color: f.confidence > 0.9 ? "#22c55e" : "#f59e0b",
                  }}>{(f.confidence * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div style={{ ...cardStyle, padding: 16, marginBottom: 12 }}>
              <div style={{ color: "#a855f7", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>Similar Cases (KNN Evidence)</div>
              <div style={{ color: v("--text-secondary"), fontSize: 11 }}>Found {radiologyReport.similarCases} similar cases in MedImageInsight vector database.</div>
              <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
                {[1, 2, 3, 4].slice(0, radiologyReport.similarCases).map(n => (
                  <div key={n} style={{
                    width: 48, height: 48, borderRadius: 6,
                    background: v("--bg-tertiary"), border: `1px solid ${v("--border")}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: v("--text-muted"), fontSize: 9,
                  }}>Case {n}</div>
                ))}
              </div>
            </div>
            <div style={{ ...cardStyle, padding: 16, marginBottom: 12, borderLeft: "3px solid #22c55e" }}>
              <div style={{ color: "#22c55e", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Recommendation</div>
              <div style={{ color: v("--text-primary"), fontSize: 11 }}>{radiologyReport.recommendation}</div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button style={{ flex: 1, padding: "9px", borderRadius: 6, border: "none", background: "#22c55e", color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>✓ Approve</button>
              <button style={{ flex: 1, padding: "9px", borderRadius: 6, border: `1px solid ${accentBg("#f59e0b", 0.3)}`, background: "transparent", color: "#f59e0b", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>⚑ Flag</button>
              <button style={{ flex: 1, padding: "9px", borderRadius: 6, border: `1px solid ${v("--border")}`, background: "transparent", color: v("--text-secondary"), fontSize: 11, cursor: "pointer" }}>↗ Reassign</button>
            </div>
          </div>
        </div>
        <div style={{
          marginTop: 12, padding: 10, borderRadius: 6,
          background: accentBg("#00b4d8", 0.05), border: `1px solid ${accentBg("#00b4d8", 0.15)}`,
        }}>
          <div style={{ color: "#00b4d8", fontSize: 10, fontWeight: 600 }}>⚠️ AI-ASSISTED ANALYSIS — REQUIRES RADIOLOGIST REVIEW</div>
        </div>
      </div>
    );
  };

  // ── Vitals View ───────────────────────────────────────────────
  const VitalsView = () => {
    if (!vitals) {
      return <div style={{ padding: 40, textAlign: "center", color: v("--text-muted"), fontSize: 14 }}>Loading vitals...</div>;
    }

    return (
      <div style={{ padding: "32px 36px", fontFamily: appFontStack }}>
        <h2 style={{ color: "#a855f7", margin: "0 0 20px", fontSize: 24, fontWeight: 700, fontFamily: headingFont }}>📊 Patient Vitals Monitor</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
          {[
            { label: "Heart Rate", value: `${vitals.hr} bpm`, color: "#ef4444", range: "60-100", icon: "❤️" },
            { label: "Blood Pressure", value: vitals.bp, color: "#f59e0b", range: "120/80", icon: "🩸" },
            { label: "SpO2", value: `${vitals.spo2}%`, color: "#00b4d8", range: ">95%", icon: "🫁" },
            { label: "Temperature", value: `${vitals.temp}°C`, color: "#22c55e", range: "36.5-37.5", icon: "🌡️" },
            { label: "Resp. Rate", value: `${vitals.rr}/min`, color: "#a855f7", range: "12-20", icon: "💨" },
            { label: "MEWS Score", value: vitals.mews, color: vitals.mews < 3 ? "#22c55e" : "#ef4444", range: "0-2 Normal", icon: "📈" },
          ].map(item => (
            <div key={item.label} style={{ ...cardStyle, padding: 14, borderLeft: `3px solid ${item.color}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 24 }}>{item.icon}</span>
                <span style={{ color: v("--text-muted"), fontSize: 10 }}>Normal: {item.range}</span>
              </div>
              <div style={{ color: item.color, fontSize: 32, fontWeight: 700, marginTop: 6 }}>{item.value}</div>
              <div style={{ color: v("--text-secondary"), fontSize: 12 }}>{item.label}</div>
            </div>
          ))}
        </div>
        <div style={{ ...cardStyle, padding: 16 }}>
          <div style={{ color: "#a855f7", fontSize: 12, fontWeight: 600, marginBottom: 10 }}>Trend Analysis (Last 6 Hours)</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 60 }}>
            {[65, 72, 68, 88, 82, 78, 85, 88, 92, 86, 88, 84].map((val, i) => (
              <div key={i} style={{
                flex: 1, height: `${(val / 100) * 60}px`,
                background: val > 85 ? accentBg("#f59e0b", 0.25) : accentBg("#a855f7", 0.2),
                borderRadius: "2px 2px 0 0", position: "relative",
              }}>
                {i === 11 && <div style={{ position: "absolute", top: -14, left: "50%", transform: "translateX(-50%)", color: "#a855f7", fontSize: 8 }}>{val}</div>}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ color: v("--text-muted"), fontSize: 8 }}>-6h</span>
            <span style={{ color: v("--text-muted"), fontSize: 8 }}>-3h</span>
            <span style={{ color: v("--text-muted"), fontSize: 8 }}>Now</span>
          </div>
        </div>
      </div>
    );
  };

  // ── Template Renderers ─────────────────────────────────────
  const renderCardComponent = (spec) => {
    const accent = spec.styling?.accent_color || "#8b5cf6";
    const items = spec.data || [];
    const isGrid = spec.styling?.layout === "grid";
    return (
      <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}` }}>
        <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{spec.title}</div>
        {spec.description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{spec.description}</div>}
        <div style={{ display: "grid", gridTemplateColumns: isGrid ? "repeat(auto-fill, minmax(160px, 1fr))" : "1fr", gap: 10 }}>
          {items.map((item, i) => (
            <div key={i} style={{ ...cardStyle, padding: 14, borderLeft: `3px solid ${item.color || accent}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {item.icon && <span style={{ fontSize: 22 }}>{item.icon}</span>}
                <div>
                  <div style={{ color: v("--text-muted"), fontSize: 10 }}>{item.label}</div>
                  <div style={{ color: item.color || accent, fontSize: 18, fontWeight: 700 }}>{item.value}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderStatGrid = (spec) => {
    const accent = spec.styling?.accent_color || "#8b5cf6";
    const items = spec.data || [];
    return (
      <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}` }}>
        <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{spec.title}</div>
        {spec.description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{spec.description}</div>}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12 }}>
          {items.map((item, i) => {
            const color = item.color || accent;
            return (
              <div key={i} style={{ ...cardStyle, padding: 16, textAlign: "center" }}>
                {item.icon && <div style={{ fontSize: 28, marginBottom: 4 }}>{item.icon}</div>}
                <div style={{ color, fontSize: 26, fontWeight: 700 }}>{item.value}</div>
                <div style={{ color: v("--text-muted"), fontSize: 11, marginTop: 2 }}>{item.label}</div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderTableComponent = (spec) => {
    const accent = spec.styling?.accent_color || "#8b5cf6";
    const cols = spec.columns || [];
    const rows = spec.data || [];
    return (
      <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}`, overflow: "auto" }}>
        <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{spec.title}</div>
        {spec.description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{spec.description}</div>}
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr>
              {cols.map(col => (
                <th key={col.key} style={{ textAlign: "left", padding: "8px 12px", borderBottom: `2px solid ${accent}`, color: accent, fontWeight: 600, fontSize: 11, textTransform: "uppercase" }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {cols.map(col => (
                  <td key={col.key} style={{ padding: "8px 12px", borderBottom: `1px solid ${v("--border")}`, color: v("--text-primary") }}>
                    {row[col.key] ?? "—"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderFormComponent = (spec) => {
    const accent = spec.styling?.accent_color || "#8b5cf6";
    const fields = spec.fields || [];
    return (
      <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}` }}>
        <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{spec.title}</div>
        {spec.description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{spec.description}</div>}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {fields.map((f, i) => (
            <div key={i}>
              <label style={{ display: "block", color: v("--text-secondary"), fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{f.label}</label>
              {f.type === "textarea" ? (
                <textarea style={{ width: "100%", padding: 10, borderRadius: 6, border: `1px solid ${v("--border")}`, background: v("--input-bg"), color: v("--text-primary"), fontSize: 13, fontFamily: appFontStack, minHeight: 60 }} placeholder={f.label} />
              ) : f.type === "select" ? (
                <select style={{ width: "100%", padding: 10, borderRadius: 6, border: `1px solid ${v("--border")}`, background: v("--input-bg"), color: v("--text-primary"), fontSize: 13 }}>
                  {(f.options || []).map((opt, j) => <option key={j} value={opt}>{opt}</option>)}
                </select>
              ) : (
                <input type={f.type || "text"} style={{ width: "100%", padding: 10, borderRadius: 6, border: `1px solid ${v("--border")}`, background: v("--input-bg"), color: v("--text-primary"), fontSize: 13 }} placeholder={f.label} />
              )}
            </div>
          ))}
          <button style={{ padding: "10px 20px", borderRadius: 6, border: "none", background: accent, color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer", alignSelf: "flex-start" }}>Submit</button>
        </div>
      </div>
    );
  };

  const renderListComponent = (spec) => {
    const accent = spec.styling?.accent_color || "#8b5cf6";
    const items = spec.data || [];
    return (
      <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}` }}>
        <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{spec.title}</div>
        {spec.description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{spec.description}</div>}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {items.map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 8, background: v("--bg-secondary"), border: `1px solid ${v("--border")}` }}>
              {item.icon && <span style={{ fontSize: 20 }}>{item.icon}</span>}
              <div style={{ flex: 1 }}>
                <div style={{ color: v("--text-primary"), fontSize: 13, fontWeight: 600 }}>{item.label || item.name || item.title}</div>
                {item.value && <div style={{ color: v("--text-muted"), fontSize: 11 }}>{item.value}</div>}
              </div>
              {item.status && <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 10, background: accentBg(accent, 0.1), color: accent }}>{item.status}</span>}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderGeneratedComponent = (spec) => {
    if (!spec) return null;
    switch (spec.component_type) {
      case "card": return renderCardComponent(spec);
      case "stat_grid": return renderStatGrid(spec);
      case "table": return renderTableComponent(spec);
      case "form": return renderFormComponent(spec);
      case "list": return renderListComponent(spec);
      case "chart": return renderStatGrid(spec); // charts fall back to stat_grid
      default: return renderCardComponent(spec);
    }
  };

  // ── GenUI Send Handler ───────────────────────────────────
  const handleGenUISend = useCallback(async () => {
    if (!genUIInput.trim()) return;
    const userMessage = genUIInput;
    dispatchGenUI({ type: "ADD", payload: { role: "user", text: userMessage } });
    setGenUIInput("");
    dispatchGenUI({ type: "ADD", payload: { role: "assistant", text: "", streaming: true } });

    try {
      let fullResponse = "";
      const editCtx = editingItemId
        ? { editing: true, existing_spec: canvasItems.find(c => c.id === editingItemId)?.spec }
        : {};
      await api.chatWithAgent(
        "genui",
        userMessage,
        editCtx,
        (chunk) => {
          fullResponse += chunk;
          dispatchGenUI({ type: "UPDATE_LAST", payload: { role: "assistant", text: fullResponse, streaming: true } });
        },
        (err) => {
          dispatchGenUI({ type: "UPDATE_LAST", payload: { role: "assistant", text: `[ERROR] ${err.message}`, streaming: false } });
        }
      );
      const wasEditing = !!editingItemId;
      dispatchGenUI({ type: "UPDATE_LAST", payload: { role: "assistant", text: fullResponse, wasEdit: wasEditing } });
      // Auto-add or update canvas item
      const spec = tryExtractComponentSpec(fullResponse);
      if (spec) {
        if (editingItemId) {
          setCanvasItems(prev => prev.map(c => c.id === editingItemId ? { ...c, spec } : c));
          setEditingItemId(null);
        } else {
          setCanvasItems(prev => [...prev, { id: "c-" + Date.now() + "-" + Math.random().toString(36).slice(2, 6), spec }]);
        }
      } else if (editingItemId) {
        setEditingItemId(null);
      }
    } catch (err) {
      dispatchGenUI({ type: "UPDATE_LAST", payload: { role: "assistant", text: `[ERROR] ${err.message}` } });
      if (editingItemId) setEditingItemId(null);
    }
  }, [genUIInput, editingItemId, canvasItems]);

  // Auto-scroll GenUI chat
  useEffect(() => {
    if (genUIChatRef.current) {
      genUIChatRef.current.scrollTop = genUIChatRef.current.scrollHeight;
    }
  }, [genUIMessages]);

  // ── Floating GenUI Widget ──────────────────────────────────
  const GenUIWidget = () => {
    if (!genUIOpen) {
      // Collapsed: floating button
      return (
        <button
          onClick={() => setGenUIOpen(true)}
          style={{
            position: "fixed", bottom: 24, right: 24, zIndex: 1000,
            width: 56, height: 56, borderRadius: "50%",
            background: "#8b5cf6", border: "none",
            boxShadow: "0 4px 20px rgba(139,92,246,0.4)",
            cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 26, color: "#fff",
            transition: "transform 0.2s, box-shadow 0.2s",
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.08)"; e.currentTarget.style.boxShadow = "0 6px 28px rgba(139,92,246,0.55)"; }}
          onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(139,92,246,0.4)"; }}
          title="GenUI Agent"
        >
          🎨
        </button>
      );
    }

    // Expanded: chat panel
    return (
      <div style={{
        position: "fixed", bottom: 24, right: 24, zIndex: 1000,
        width: 420, height: 560,
        borderRadius: 16, overflow: "hidden",
        background: v("--card-bg"),
        border: `1px solid ${v("--border")}`,
        boxShadow: "0 8px 40px rgba(0,0,0,0.2)",
        display: "flex", flexDirection: "column",
        fontFamily: appFontStack,
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "14px 18px",
          borderBottom: `1px solid ${v("--border")}`,
          background: v("--bg-secondary"),
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>🎨</span>
            <div>
              <div style={{ color: "#8b5cf6", fontWeight: 700, fontSize: 14, fontFamily: headingFont }}>GenUI Agent</div>
              <div style={{ color: v("--text-muted"), fontSize: 10 }}>Describe a UI to generate</div>
            </div>
          </div>
          <button
            onClick={() => setGenUIOpen(false)}
            style={{
              background: "transparent", border: "none",
              color: v("--text-muted"), fontSize: 20, cursor: "pointer",
              width: 32, height: 32, borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
            onMouseEnter={e => e.currentTarget.style.background = v("--hover-bg")}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            ×
          </button>
        </div>

        {/* Chat messages */}
        <div ref={genUIChatRef} style={{ flex: 1, overflowY: "auto", padding: "16px 18px" }}>
          {genUIMessages.map((m, i) => {
            if (m.role === "user") {
              return (
                <div key={i} style={{ marginBottom: 14, display: "flex", justifyContent: "flex-end" }}>
                  <div style={{
                    maxWidth: "80%", padding: "8px 14px", borderRadius: "14px 14px 4px 14px",
                    background: v("--user-msg-bg"), color: v("--user-msg-text"),
                    fontSize: 13, lineHeight: 1.5,
                  }}>{m.text}</div>
                </div>
              );
            }
            // assistant
            const spec = (!m.streaming) ? tryExtractComponentSpec(m.text) : null;
            if (m.streaming) {
              return (
                <div key={i} style={{ marginBottom: 14 }}>
                  <div style={{ color: "#8b5cf6", fontSize: 10, fontWeight: 600, marginBottom: 6 }}>
                    GenUI Agent <span style={{ color: v("--text-muted"), fontWeight: 400 }}>is generating...</span>
                  </div>
                  {SkeletonCard()}
                </div>
              );
            }
            return (
              <div key={i} style={{ marginBottom: 14 }}>
                {spec ? (
                  renderGeneratedComponent(spec)
                ) : (
                  <div style={{ color: v("--text-primary"), fontSize: 13, lineHeight: 1.6 }}>{m.text}</div>
                )}
              </div>
            );
          })}
        </div>

        {/* Quick chips (only if no user messages yet) */}
        {genUIMessages.filter(m => m.role === "user").length === 0 && (
          <div style={{ padding: "0 18px 10px", display: "flex", gap: 6, flexWrap: "wrap" }}>
            {["patient vitals", "appointment form", "medication list", "weather card"].map(p => (
              <button key={p} onClick={() => { setGenUIInput(p); }}
                style={{
                  padding: "4px 10px", borderRadius: 14,
                  border: `1px solid ${v("--border")}`, background: "transparent",
                  color: v("--text-secondary"), fontSize: 11, cursor: "pointer",
                }}>{p}</button>
            ))}
          </div>
        )}

        {/* Input area */}
        <div style={{
          padding: "12px 18px",
          borderTop: `1px solid ${v("--border")}`,
          display: "flex", gap: 8, alignItems: "flex-end",
        }}>
          <textarea
            dir="ltr"
            value={genUIInput}
            onChange={e => setGenUIInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleGenUISend(); } }}
            placeholder="Describe a component..."
            rows={1}
            style={{
              flex: 1, padding: "10px 12px", borderRadius: 10,
              border: `1px solid ${v("--input-border")}`, background: v("--input-bg"),
              color: v("--text-primary"), fontSize: 13, fontFamily: appFontStack,
              resize: "none", outline: "none", lineHeight: 1.4,
              maxHeight: 80,
            }}
          />
          <button
            onClick={handleGenUISend}
            disabled={!genUIInput.trim()}
            style={{
              width: 38, height: 38, borderRadius: 10, flexShrink: 0,
              border: "none", background: "#8b5cf6", color: "#fff",
              fontSize: 16, cursor: genUIInput.trim() ? "pointer" : "not-allowed",
              opacity: genUIInput.trim() ? 1 : 0.4,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >
            ↑
          </button>
        </div>
      </div>
    );
  };

  // ── Canvas View (split: chat left, canvas right) ────────────
  const CanvasView = () => (
    <div style={{ display: "flex", height: "100%", fontFamily: appFontStack }}>
      {/* Left panel — GenUI Chat */}
      <div style={{
        width: 380, display: "flex", flexDirection: "column",
        borderRight: `1px solid ${v("--border")}`,
        background: v("--bg-secondary"),
      }}>
        {/* Chat header */}
        <div style={{
          padding: "14px 18px",
          borderBottom: `1px solid ${v("--border")}`,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <span style={{ fontSize: 22 }}>🎨</span>
          <div>
            <div style={{ color: "#8b5cf6", fontWeight: 700, fontSize: 14, fontFamily: headingFont }}>GenUI Agent</div>
            <div style={{ color: v("--text-muted"), fontSize: 10 }}>Describe a component to generate</div>
          </div>
        </div>

        {/* Chat messages */}
        <div ref={genUIChatRef} style={{ flex: 1, overflowY: "auto", padding: "16px 18px" }}>
          {genUIMessages.map((m, i) => {
            if (m.role === "user") {
              return (
                <div key={i} style={{ marginBottom: 14, display: "flex", justifyContent: "flex-end" }}>
                  <div style={{
                    maxWidth: "80%", padding: "8px 14px", borderRadius: "14px 14px 4px 14px",
                    background: v("--user-msg-bg"), color: v("--user-msg-text"),
                    fontSize: 13, lineHeight: 1.5,
                  }}>{m.text}</div>
                </div>
              );
            }
            // assistant
            const spec = (!m.streaming) ? tryExtractComponentSpec(m.text) : null;
            if (m.streaming) {
              return (
                <div key={i} style={{ marginBottom: 14 }}>
                  <div style={{ color: "#8b5cf6", fontSize: 10, fontWeight: 600, marginBottom: 6 }}>
                    GenUI Agent <span style={{ color: v("--text-muted"), fontWeight: 400 }}>is generating...</span>
                  </div>
                  {SkeletonCard()}
                </div>
              );
            }
            return (
              <div key={i} style={{ marginBottom: 14 }}>
                {spec ? (
                  <div style={{
                    padding: "8px 10px", borderRadius: 8,
                    background: accentBg("#8b5cf6", 0.06),
                    border: `1px solid ${accentBg("#8b5cf6", 0.15)}`,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      <span style={{ color: "#22c55e", fontSize: 12 }}>✓</span>
                      <span style={{ color: "#8b5cf6", fontSize: 11, fontWeight: 600 }}>{spec.title || spec.component_type}</span>
                      <span style={{ color: v("--text-muted"), fontSize: 10 }}>{m.wasEdit ? "updated on canvas" : "added to canvas"}</span>
                    </div>
                    <div style={{ color: v("--text-muted"), fontSize: 10 }}>
                      Type: {spec.component_type} {spec.data ? `• ${spec.data.length} items` : ""}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: v("--text-primary"), fontSize: 13, lineHeight: 1.6 }}>{m.text}</div>
                )}
              </div>
            );
          })}
        </div>

        {/* Quick chips */}
        {genUIMessages.filter(m => m.role === "user").length === 0 && (
          <div style={{ padding: "0 18px 10px", display: "flex", gap: 6, flexWrap: "wrap" }}>
            {["patient vitals", "appointment form", "medication list", "weather card"].map(p => (
              <button key={p} onClick={() => setGenUIInput(p)}
                style={{
                  padding: "4px 10px", borderRadius: 14,
                  border: `1px solid ${v("--border")}`, background: "transparent",
                  color: v("--text-secondary"), fontSize: 11, cursor: "pointer",
                }}>{p}</button>
            ))}
          </div>
        )}

        {/* Editing indicator */}
        {editingItemId && (
          <div style={{
            padding: "6px 18px", display: "flex", alignItems: "center", justifyContent: "space-between",
            background: accentBg("#8b5cf6", 0.1),
            borderTop: `1px solid ${accentBg("#8b5cf6", 0.2)}`,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 11 }}>&#9998;</span>
              <span style={{ color: "#8b5cf6", fontSize: 11, fontWeight: 600 }}>
                Editing: {canvasItems.find(c => c.id === editingItemId)?.spec?.title || "component"}
              </span>
            </div>
            <button
              onClick={() => { setEditingItemId(null); setGenUIInput(""); }}
              style={{
                background: "transparent", border: "none",
                color: v("--text-muted"), fontSize: 14, cursor: "pointer", padding: "2px 6px",
              }}
            >×</button>
          </div>
        )}

        {/* Input */}
        <div style={{
          padding: "12px 18px",
          borderTop: editingItemId ? "none" : `1px solid ${v("--border")}`,
          display: "flex", gap: 8, alignItems: "flex-end",
        }}>
          <textarea
            dir="ltr"
            value={genUIInput}
            onChange={e => setGenUIInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleGenUISend(); } }}
            placeholder={editingItemId ? "Describe what to change..." : "Describe a component..."}
            rows={1}
            style={{
              flex: 1, padding: "10px 12px", borderRadius: 10,
              border: `1px solid ${editingItemId ? "#8b5cf6" : v("--input-border")}`, background: v("--input-bg"),
              color: v("--text-primary"), fontSize: 13, fontFamily: appFontStack,
              resize: "none", outline: "none", lineHeight: 1.4, maxHeight: 80,
            }}
          />
          <button
            onClick={handleGenUISend}
            disabled={!genUIInput.trim()}
            style={{
              width: 38, height: 38, borderRadius: 10, flexShrink: 0,
              border: "none", background: "#8b5cf6", color: "#fff",
              fontSize: 16, cursor: genUIInput.trim() ? "pointer" : "not-allowed",
              opacity: genUIInput.trim() ? 1 : 0.4,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >↑</button>
        </div>
      </div>

      {/* Right panel — Canvas */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "24px 28px",
        background: v("--bg-primary"),
        backgroundImage: `radial-gradient(circle, ${v("--border")} 1px, transparent 1px)`,
        backgroundSize: "24px 24px",
      }}>
        {canvasItems.length === 0 ? (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            height: "100%", textAlign: "center",
          }}>
            <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🎨</div>
            <div style={{ color: v("--text-secondary"), fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              Your canvas is empty
            </div>
            <div style={{ color: v("--text-muted"), fontSize: 13, lineHeight: 1.6, maxWidth: 320 }}>
              Type a prompt in the chat on the left to generate UI components. They'll appear here automatically. Click any component to edit it.
            </div>
          </div>
        ) : (
          <div>
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20,
            }}>
              <div>
                <h2 style={{ color: v("--text-primary"), margin: 0, fontSize: 20, fontWeight: 700, fontFamily: headingFont }}>Canvas</h2>
                <div style={{ color: v("--text-muted"), fontSize: 12, marginTop: 2 }}>
                  {canvasItems.length} component{canvasItems.length !== 1 ? "s" : ""}
                </div>
              </div>
              <button
                onClick={() => setCanvasItems([])}
                style={{
                  padding: "6px 14px", borderRadius: 6,
                  border: `1px solid ${v("--border")}`, background: "transparent",
                  color: v("--text-secondary"), fontSize: 11, cursor: "pointer",
                }}
              >Clear All</button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              {canvasItems.map(item => {
                const isEditing = editingItemId === item.id;
                const itemWidth = item.width || "100%";
                return (
                  <div key={item.id} style={{
                    position: "relative",
                    width: itemWidth,
                    minWidth: 280,
                    maxWidth: "100%",
                    outline: isEditing ? "2px solid #8b5cf6" : "2px solid transparent",
                    borderRadius: 12,
                    cursor: "pointer",
                    transition: "outline 0.15s",
                  }}
                    onClick={() => {
                      if (!isEditing) {
                        setEditingItemId(item.id);
                        setGenUIInput(`Update "${item.spec.title || item.spec.component_type}": `);
                      }
                    }}
                  >
                    {/* Toolbar */}
                    <div style={{
                      position: "absolute", top: -14, right: 12, zIndex: 2,
                      display: "flex", gap: 4, alignItems: "center",
                      opacity: isEditing ? 1 : 0,
                      transition: "opacity 0.15s",
                      pointerEvents: isEditing ? "auto" : "none",
                    }}>
                      {/* Size controls */}
                      {["50%", "75%", "100%"].map(w => (
                        <button key={w}
                          onClick={(e) => {
                            e.stopPropagation();
                            setCanvasItems(prev => prev.map(c => c.id === item.id ? { ...c, width: w } : c));
                          }}
                          style={{
                            padding: "3px 8px", borderRadius: 6,
                            border: `1px solid ${itemWidth === w ? "#8b5cf6" : v("--border")}`,
                            background: itemWidth === w ? accentBg("#8b5cf6", 0.15) : v("--card-bg"),
                            color: itemWidth === w ? "#8b5cf6" : v("--text-muted"),
                            fontSize: 10, fontWeight: 600, cursor: "pointer",
                            fontFamily: appFontStack,
                          }}
                        >{w}</button>
                      ))}
                      <div style={{ width: 1, height: 16, background: v("--border"), margin: "0 2px" }} />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingItemId(null);
                          setGenUIInput("");
                        }}
                        style={{
                          padding: "3px 10px", borderRadius: 6,
                          border: `1px solid #8b5cf6`, background: "#8b5cf6",
                          color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer",
                          fontFamily: appFontStack,
                        }}
                      >Editing</button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingItemId(null);
                          setCanvasItems(prev => prev.filter(c => c.id !== item.id));
                        }}
                        title="Remove component"
                        style={{
                          padding: "3px 8px", borderRadius: 6,
                          border: `1px solid ${v("--border")}`, background: v("--card-bg"),
                          color: v("--text-muted"), fontSize: 12, cursor: "pointer",
                          fontFamily: appFontStack,
                        }}
                      >×</button>
                    </div>
                    {renderGeneratedComponent(item.spec)}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // ── Agent Chat View (CopilotKit-style) ────────────────────────
  const AgentView = () => (
    <div style={{ display: "flex", height: "calc(100% - 48px)", fontFamily: appFontStack }}>
      {/* Sidebar */}
      <div style={{
        width: 240, borderRight: `1px solid ${v("--border")}`,
        padding: 16, display: "flex", flexDirection: "column",
        background: v("--bg-secondary"),
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
          <span style={{ fontSize: 28 }}>{selectedAgent.icon}</span>
          <div>
            <div style={{ color: selectedAgent.color, fontWeight: 700, fontSize: 15, fontFamily: headingFont }}>{selectedAgent.name}</div>
            <div style={{ color: v("--text-muted"), fontSize: 10 }}>SKILL.md loaded</div>
          </div>
        </div>
        <div style={{ color: v("--text-muted"), fontSize: 11, marginBottom: 6, fontWeight: 600 }}>SKILLS</div>
        {selectedAgent.skills.map(s => (
          <button key={s} style={{
            display: "block", width: "100%", padding: "8px 10px", marginBottom: 4,
            borderRadius: 6, border: `1px solid ${v("--border")}`,
            background: v("--card-bg"),
            color: v("--text-primary"), fontSize: 12, cursor: "pointer",
            textAlign: "left", fontFamily: appFontStack,
          }}>{s}</button>
        ))}
        <div style={{
          marginTop: "auto", padding: 10, borderRadius: 8,
          background: v("--bg-tertiary"), border: `1px solid ${v("--border")}`,
        }}>
          <div style={{ color: v("--text-muted"), fontSize: 10, marginBottom: 4, fontWeight: 600 }}>AGENT INFO</div>
          <div style={{ color: v("--text-secondary"), fontSize: 11 }}>Queue: {selectedAgent.queue} items</div>
          <div style={{ color: v("--text-secondary"), fontSize: 11 }}>Status: {selectedAgent.status}</div>
          <div style={{ color: v("--text-secondary"), fontSize: 11 }}>Model: {selectedAgent.models_used ? selectedAgent.models_used[0] : "Claude"}</div>
        </div>
      </div>

      {/* Chat area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", background: v("--bg-primary") }}>
        <div style={{ flex: 1, padding: "24px 32px", overflowY: "auto" }}>
          {chatMessages.map((m, i) => {
            if (m.role === "system") {
              return (
                <div key={i} style={{ textAlign: "center", marginBottom: 20 }}>
                  <span style={{ color: v("--text-muted"), fontSize: 12, fontStyle: "italic" }}>{m.text}</span>
                </div>
              );
            }
            if (m.role === "user") {
              return (
                <div key={i} style={{ marginBottom: 16, display: "flex", justifyContent: "flex-end" }}>
                  <div style={{
                    maxWidth: "70%", padding: "10px 16px", borderRadius: "16px 16px 4px 16px",
                    background: v("--user-msg-bg"), color: v("--user-msg-text"),
                    fontSize: 14, lineHeight: 1.5,
                  }}>{m.text}</div>
                </div>
              );
            }
            // assistant — check for GenUI component spec
            const isGenUI = selectedAgent.id === "genui";
            const componentSpec = (!m.streaming && isGenUI) ? tryExtractComponentSpec(m.text) : null;

            // GenUI agent: show skeleton while streaming, rendered component when done
            if (isGenUI && m.streaming) {
              return (
                <div key={i} style={{ marginBottom: 16 }}>
                  <div style={{ color: selectedAgent.color, fontSize: 11, fontWeight: 600, marginBottom: 8, fontFamily: headingFont }}>
                    {selectedAgent.name} <span style={{ color: v("--text-muted"), fontWeight: 400 }}>is generating a component...</span>
                  </div>
                  {SkeletonCard()}
                </div>
              );
            }

            return (
              <div key={i} style={{ marginBottom: 16 }}>
                <div style={{ color: selectedAgent.color, fontSize: 11, fontWeight: 600, marginBottom: 4, fontFamily: headingFont }}>{selectedAgent.name}</div>
                {componentSpec ? (
                  <div style={{ maxWidth: "90%" }}>
                    {renderGeneratedComponent(componentSpec)}
                  </div>
                ) : m.streaming && !m.text ? (
                  <div style={{ padding: "8px 0" }}>
                    <span style={{ color: v("--text-muted"), fontSize: 20, letterSpacing: 2 }}>• • •</span>
                  </div>
                ) : (
                  <div style={{
                    maxWidth: "80%",
                    color: v("--text-primary"), fontSize: 14, lineHeight: 1.6,
                  }}>
                    {m.text}{m.streaming && <span style={{ color: v("--text-muted") }}> ▊</span>}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Upload bar */}
        <div style={{ padding: "8px 32px", borderTop: `1px solid ${v("--border")}`, display: "flex", gap: 4, flexWrap: "wrap" }}>
          <input id="fileUpload" type="file" multiple accept="image/*,.pdf,.doc,.docx,.txt" style={{ display: "none" }} onChange={(e) => {
            const files = e.target.files;
            if (files && files.length > 0) {
              setInputText(prev => prev + (prev ? "\n" : "") + `📎 Attached: ${Array.from(files).map(f => f.name).join(", ")}`);
            }
          }} />
          <button onClick={() => document.getElementById("fileUpload").click()}
            style={{
              padding: "6px 12px", borderRadius: 6,
              border: `1px solid ${v("--border")}`,
              background: "transparent", color: selectedAgent.color,
              fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: appFontStack,
            }}>📎 Upload</button>
        </div>

        <InputArea value={inputText} onChange={e => setInputText(e.target.value)} onSend={handleSend} agentName={selectedAgent.name} agentColor={selectedAgent.color} textareaRef={textareaRef} />
      </div>
    </div>
  );

  // ── Main render ───────────────────────────────────────────────
  return (
    <div style={{
      height: "100vh",
      background: v("--bg-primary"),
      fontFamily: appFontStack,
      color: v("--text-primary"),
      overflow: "hidden",
      transition: "background 0.2s, color 0.2s",
    }}>
      {NavBar()}
      {ErrorBanner()}
      <div style={{ height: "calc(100vh - 48px)", overflowY: activeView === "canvas" ? "hidden" : "auto" }}>
        {activeView === "dashboard" && Dashboard()}
        {activeView === "triage" && TriageView()}
        {activeView === "radiology" && RadiologyView()}
        {activeView === "vitals" && VitalsView()}
        {activeView === "canvas" && CanvasView()}
        {activeView === "agent" && selectedAgent && AgentView()}
      </div>
      {activeView !== "canvas" && GenUIWidget()}
    </div>
  );
}
