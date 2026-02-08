import { useState, useEffect } from "react";
import * as api from "../services/api";

export default function MedAssistDashboard() {
  // State management
  const [activeView, setActiveView] = useState("dashboard");
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [inputText, setInputText] = useState("");

  // API data state
  const [agents, setAgents] = useState([]);
  const [triagePatients, setTriagePatients] = useState([]);
  const [radiologyReport, setRadiologyReport] = useState(null);
  const [vitals, setVitals] = useState(null);

  // Error state
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch agents on mount
  useEffect(() => {
    async function fetchAgents() {
      try {
        setLoading(true);
        setError(null);
        const agentsData = await api.getAgents();
        // Map backend agent_id to frontend id field for compatibility
        const mappedAgents = agentsData.map(agent => ({
          ...agent,
          id: agent.agent_id,
          bg: getBgColor(agent.color),
        }));
        setAgents(mappedAgents);
      } catch (err) {
        console.error("Failed to fetch agents:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchAgents();
  }, []);

  // Fetch triage queue when triage view is active
  useEffect(() => {
    if (activeView === "triage") {
      async function fetchTriageQueue() {
        try {
          setError(null);
          const queue = await api.getTriageQueue();
          setTriagePatients(queue);
        } catch (err) {
          console.error("Failed to fetch triage queue:", err);
          setError(err.message);
        }
      }
      fetchTriageQueue();
    }
  }, [activeView]);

  // Fetch radiology report when radiology view is active
  useEffect(() => {
    if (activeView === "radiology") {
      async function fetchRadiologyReport() {
        try {
          setError(null);
          const report = await api.getLatestRadiologyReport();
          setRadiologyReport(report);
        } catch (err) {
          console.error("Failed to fetch radiology report:", err);
          setError(err.message);
        }
      }
      fetchRadiologyReport();
    }
  }, [activeView]);

  // Fetch vitals when vitals view is active
  useEffect(() => {
    if (activeView === "vitals") {
      async function fetchVitals() {
        try {
          setError(null);
          const vitalsData = await api.getLatestVitals();
          setVitals(vitalsData);
        } catch (err) {
          console.error("Failed to fetch vitals:", err);
          setError(err.message);
        }
      }
      fetchVitals();
    }
  }, [activeView]);

  // Helper to generate background color from accent color
  function getBgColor(color) {
    // Convert hex color to dark background variant
    const colorMap = {
      "#ef4444": "#1a0505",
      "#00b4d8": "#051a1f",
      "#22c55e": "#051a0a",
      "#f59e0b": "#1a1405",
      "#a855f7": "#0f051a",
      "#06b6d4": "#051519",
      "#10b981": "#051a12",
      "#e879f9": "#19051a",
    };
    return colorMap[color] || "#0e1a2e";
  }

  const handleAgentClick = (agent) => {
    setSelectedAgent(agent);
    setActiveView("agent");
    setChatMessages([
      { role: "system", text: `${agent.name} activated. Ready to assist.` },
      {
        role: "assistant",
        text: `Hello! I'm the ${agent.name}. How can I help you today? My available skills are: ${agent.skills.join(", ")}.`
      }
    ]);
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    // Add user message
    const userMessage = inputText;
    setChatMessages(prev => [...prev, { role: "user", text: userMessage }]);
    setInputText("");

    // Add placeholder for assistant response
    setChatMessages(prev => [...prev, { role: "assistant", text: "", streaming: true }]);

    try {
      let fullResponse = "";

      await api.chatWithAgent(
        selectedAgent.id,
        userMessage,
        {},
        (chunk) => {
          fullResponse += chunk;
          setChatMessages(prev => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg.streaming) {
              lastMsg.text = fullResponse;
            }
            return updated;
          });
        },
        (error) => {
          console.error("Chat error:", error);
          setChatMessages(prev => {
            const updated = [...prev];
            const lastMsg = updated[updated.length - 1];
            if (lastMsg.streaming) {
              lastMsg.text = `[ERROR] ${error.message}`;
              lastMsg.streaming = false;
            }
            return updated;
          });
        }
      );

      // Mark streaming complete
      setChatMessages(prev => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg.streaming) {
          delete lastMsg.streaming;
        }
        return updated;
      });
    } catch (err) {
      console.error("Failed to send message:", err);
      setChatMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          text: `[ERROR] ${err.message}`
        };
        return updated;
      });
    }
  };

  // Error banner component
  const ErrorBanner = () => error && (
    <div style={{
      padding: "12px 20px",
      background: "#1a0505",
      borderBottom: "1px solid #ef444433",
      display: "flex",
      alignItems: "center",
      gap: 8
    }}>
      <span style={{ color: "#ef4444", fontSize: 14 }}>⚠️</span>
      <span style={{ color: "#ef4444", fontSize: 12 }}>{error}</span>
      <button
        onClick={() => setError(null)}
        style={{
          marginLeft: "auto",
          background: "transparent",
          border: "none",
          color: "#667788",
          cursor: "pointer",
          fontSize: 16
        }}
      >
        ×
      </button>
    </div>
  );

  const NavBar = () => (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 20px", background: "linear-gradient(90deg, #0a1628, #1a2744)", borderBottom: "1px solid #1e3a5f" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 22 }}>🏥</span>
        <span style={{ color: "#00b4d8", fontWeight: 700, fontSize: 16, letterSpacing: 0.5 }}>MedAssist AI</span>
        <span style={{ color: "#445566", fontSize: 11, marginLeft: 4 }}>OpenClaw + A2UI</span>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {["dashboard", "triage", "radiology", "vitals"].map(v => (
          <button key={v} onClick={() => { setActiveView(v); setSelectedAgent(null); }}
            style={{ padding: "5px 14px", borderRadius: 5, border: activeView === v ? "1px solid #00b4d8" : "1px solid #1e3a5f", background: activeView === v ? "#00b4d815" : "transparent", color: activeView === v ? "#00b4d8" : "#667788", fontSize: 11, cursor: "pointer", textTransform: "capitalize", fontWeight: activeView === v ? 600 : 400 }}>
            {v}
          </button>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: error ? "#ef4444" : "#22c55e", boxShadow: error ? "0 0 6px #ef4444" : "0 0 6px #22c55e" }} />
        <span style={{ color: "#667788", fontSize: 11 }}>
          {loading ? "Loading..." : error ? "Backend Error" : `${agents.filter(a => a.status === "Active").length} Agents Online`}
        </span>
      </div>
    </div>
  );

  const Dashboard = () => {
    if (loading) {
      return (
        <div style={{ padding: 20, textAlign: "center" }}>
          <div style={{ color: "#667788", fontSize: 14 }}>Loading agents...</div>
        </div>
      );
    }

    const activeAgents = agents.filter(a => a.status === "Active").length;
    const totalQueue = agents.reduce((sum, a) => sum + (a.queue || 0), 0);
    const esi1Count = triagePatients.filter(p => p.esi === 1).length || 1;

    return (
      <div style={{ padding: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <h2 style={{ color: "#e0e8f0", margin: 0, fontSize: 18 }}>Agent Control Center</h2>
            <p style={{ color: "#667788", margin: "4px 0 0", fontSize: 12 }}>
              {agents.length} specialized medical agents powered by OpenClaw
            </p>
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            {[
              { label: "Active Agents", val: `${activeAgents}/${agents.length}`, color: "#22c55e" },
              { label: "Queue Total", val: totalQueue.toString(), color: "#f59e0b" },
              { label: "ESI-1 Alerts", val: esi1Count.toString(), color: "#ef4444" }
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center", padding: "8px 16px", background: "#0e1a2e", borderRadius: 8, border: `1px solid ${s.color}22` }}>
                <div style={{ color: s.color, fontSize: 20, fontWeight: 700 }}>{s.val}</div>
                <div style={{ color: "#667788", fontSize: 10 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {agents.map(a => (
            <div key={a.id} onClick={() => handleAgentClick(a)}
              style={{ background: a.bg, border: `1px solid ${a.color}33`, borderRadius: 10, padding: 16, cursor: "pointer", transition: "all 0.2s", position: "relative", overflow: "hidden" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = a.color + "88"; e.currentTarget.style.transform = "translateY(-2px)"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = a.color + "33"; e.currentTarget.style.transform = "translateY(0)"; }}>
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: a.color, opacity: 0.7 }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 24 }}>{a.icon}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: a.status === "Active" ? "#22c55e" : "#667788" }} />
                  <span style={{ color: a.status === "Active" ? "#22c55e" : "#667788", fontSize: 9 }}>{a.status}</span>
                </div>
              </div>
              <div style={{ color: a.color, fontWeight: 600, fontSize: 13, marginBottom: 6 }}>{a.name}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
                {a.skills.slice(0, 4).map(s => (
                  <span key={s} style={{ padding: "2px 6px", borderRadius: 3, background: `${a.color}15`, color: `${a.color}cc`, fontSize: 8 }}>{s}</span>
                ))}
              </div>
              {a.queue > 0 && (
                <div style={{ color: "#667788", fontSize: 10 }}>Queue: <span style={{ color: a.color }}>{a.queue}</span> items</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const TriageView = () => (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: "#ef4444", margin: 0, fontSize: 18 }}>🚨 Triage Dashboard</h2>
        <div style={{ display: "flex", gap: 8 }}>
          {[
            { esi: "ESI-1", count: triagePatients.filter(p => p.esi === 1).length, color: "#ef4444" },
            { esi: "ESI-2", count: triagePatients.filter(p => p.esi === 2).length, color: "#f97316" },
            { esi: "ESI-3", count: triagePatients.filter(p => p.esi === 3).length, color: "#eab308" },
            { esi: "ESI-4", count: triagePatients.filter(p => p.esi === 4).length, color: "#22c55e" },
            { esi: "ESI-5", count: triagePatients.filter(p => p.esi === 5).length, color: "#3b82f6" }
          ].map(e => (
            <div key={e.esi} style={{ padding: "6px 12px", borderRadius: 6, background: `${e.color}15`, border: `1px solid ${e.color}33`, textAlign: "center" }}>
              <div style={{ color: e.color, fontSize: 16, fontWeight: 700 }}>{e.count}</div>
              <div style={{ color: "#667788", fontSize: 9 }}>{e.esi}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {triagePatients.map(p => (
          <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", background: "#0e1a2e", borderRadius: 8, borderLeft: `4px solid ${p.color}` }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: `${p.color}20`, display: "flex", alignItems: "center", justifyContent: "center", color: p.color, fontWeight: 700, fontSize: 14, flexShrink: 0 }}>
              {p.esi}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#e0e8f0", fontSize: 13, fontWeight: 600 }}>{p.name}</span>
                <span style={{ color: p.color, fontSize: 10, padding: "2px 8px", borderRadius: 10, background: `${p.color}15` }}>{p.label}</span>
              </div>
              <div style={{ color: "#8899aa", fontSize: 11, marginTop: 2 }}>{p.complaint}</div>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <div style={{ color: "#667788", fontSize: 10 }}>Wait</div>
              <div style={{ color: p.color, fontSize: 12, fontWeight: 600 }}>{p.time}</div>
            </div>
            <button style={{ padding: "6px 12px", borderRadius: 5, border: `1px solid ${p.color}44`, background: "transparent", color: p.color, fontSize: 10, cursor: "pointer" }}>View</button>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12, padding: 10, background: "#1a0505", borderRadius: 6, border: "1px solid #ef444433" }}>
        <div style={{ color: "#ef4444", fontSize: 10, fontWeight: 600, marginBottom: 4 }}>⚠️ AI-ASSISTED TRIAGE — REQUIRES CLINICIAN VERIFICATION</div>
        <div style={{ color: "#667788", fontSize: 9 }}>ESI scores are generated by ClinicalBERT + Claude API. ESI 1-2 cases auto-escalate to attending physician.</div>
      </div>
    </div>
  );

  const RadiologyView = () => {
    if (!radiologyReport) {
      return (
        <div style={{ padding: 20, textAlign: "center" }}>
          <div style={{ color: "#667788", fontSize: 14 }}>Loading radiology report...</div>
        </div>
      );
    }

    return (
      <div style={{ padding: 20 }}>
        <h2 style={{ color: "#00b4d8", margin: "0 0 16px", fontSize: 18 }}>🩻 Radiology Analysis Report</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <div style={{ background: "#0e1a2e", borderRadius: 8, padding: 16, border: "1px solid #00b4d833", marginBottom: 12 }}>
              <div style={{ color: "#667788", fontSize: 10, marginBottom: 8 }}>PATIENT INFO</div>
              <div style={{ color: "#e0e8f0", fontSize: 14, fontWeight: 600 }}>{radiologyReport.patient}</div>
              <div style={{ color: "#8899aa", fontSize: 11, marginTop: 2 }}>Modality: {radiologyReport.modality}</div>
              <div style={{ color: "#667788", fontSize: 10, marginTop: 4 }}>Model: MedImageInsight + MedGemma 4B</div>
            </div>
            <div style={{ background: "#0e1a2e", borderRadius: 8, padding: 16, border: "1px solid #00b4d833" }}>
              <div style={{ color: "#00b4d8", fontSize: 12, fontWeight: 600, marginBottom: 10 }}>Findings</div>
              {radiologyReport.findings.map((f, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: i < radiologyReport.findings.length - 1 ? "1px solid #1e3a5f" : "none" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: f.severity === "high" ? "#ef4444" : f.severity === "moderate" ? "#f59e0b" : "#22c55e", flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ color: "#ccd6e0", fontSize: 11 }}>{f.text}</div>
                  </div>
                  <div style={{ padding: "2px 8px", borderRadius: 10, background: f.confidence > 0.9 ? "#22c55e15" : "#f59e0b15", color: f.confidence > 0.9 ? "#22c55e" : "#f59e0b", fontSize: 10 }}>
                    {(f.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div style={{ background: "#0e1a2e", borderRadius: 8, padding: 16, border: "1px solid #00b4d833", marginBottom: 12 }}>
              <div style={{ color: "#a855f7", fontSize: 12, fontWeight: 600, marginBottom: 8 }}>Similar Cases (KNN Evidence)</div>
              <div style={{ color: "#8899aa", fontSize: 11 }}>Found {radiologyReport.similarCases} similar cases in MedImageInsight vector database with comparable findings pattern.</div>
              <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
                {[1, 2, 3, 4].slice(0, radiologyReport.similarCases).map(n => (
                  <div key={n} style={{ width: 50, height: 50, borderRadius: 6, background: "#1a2f4a", border: "1px solid #a855f733", display: "flex", alignItems: "center", justifyContent: "center", color: "#667788", fontSize: 9 }}>
                    Case {n}
                  </div>
                ))}
              </div>
            </div>
            <div style={{ background: "#0e1a2e", borderRadius: 8, padding: 16, border: "1px solid #22c55e33", marginBottom: 12 }}>
              <div style={{ color: "#22c55e", fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Recommendation</div>
              <div style={{ color: "#ccd6e0", fontSize: 11 }}>{radiologyReport.recommendation}</div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button style={{ flex: 1, padding: "10px", borderRadius: 6, border: "none", background: "#22c55e", color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>✓ Approve Report</button>
              <button style={{ flex: 1, padding: "10px", borderRadius: 6, border: "1px solid #f59e0b44", background: "transparent", color: "#f59e0b", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>⚑ Flag for Review</button>
              <button style={{ flex: 1, padding: "10px", borderRadius: 6, border: "1px solid #667788", background: "transparent", color: "#8899aa", fontSize: 11, cursor: "pointer" }}>↗ Reassign</button>
            </div>
          </div>
        </div>
        <div style={{ marginTop: 12, padding: 10, background: "#051a1f", borderRadius: 6, border: "1px solid #00b4d833" }}>
          <div style={{ color: "#00b4d8", fontSize: 10, fontWeight: 600 }}>⚠️ AI-ASSISTED ANALYSIS — REQUIRES RADIOLOGIST REVIEW</div>
        </div>
      </div>
    );
  };

  const VitalsView = () => {
    if (!vitals) {
      return (
        <div style={{ padding: 20, textAlign: "center" }}>
          <div style={{ color: "#667788", fontSize: 14 }}>Loading vitals...</div>
        </div>
      );
    }

    return (
      <div style={{ padding: 20 }}>
        <h2 style={{ color: "#a855f7", margin: "0 0 16px", fontSize: 18 }}>📊 Patient Vitals Monitor</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
          {[
            { label: "Heart Rate", value: `${vitals.hr} bpm`, color: "#ef4444", range: "60-100", icon: "❤️" },
            { label: "Blood Pressure", value: vitals.bp, color: "#f59e0b", range: "120/80", icon: "🩸" },
            { label: "SpO2", value: `${vitals.spo2}%`, color: "#00b4d8", range: ">95%", icon: "🫁" },
            { label: "Temperature", value: `${vitals.temp}°C`, color: "#22c55e", range: "36.5-37.5", icon: "🌡️" },
            { label: "Respiratory Rate", value: `${vitals.rr}/min`, color: "#a855f7", range: "12-20", icon: "💨" },
            { label: "MEWS Score", value: vitals.mews, color: vitals.mews < 3 ? "#22c55e" : "#ef4444", range: "0-2 Normal", icon: "📈" },
          ].map(v => (
            <div key={v.label} style={{ background: "#0e1a2e", borderRadius: 8, padding: 14, border: `1px solid ${v.color}33` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 20 }}>{v.icon}</span>
                <span style={{ color: "#667788", fontSize: 9 }}>Normal: {v.range}</span>
              </div>
              <div style={{ color: v.color, fontSize: 28, fontWeight: 700, marginTop: 6 }}>{v.value}</div>
              <div style={{ color: "#8899aa", fontSize: 11 }}>{v.label}</div>
            </div>
          ))}
        </div>
        <div style={{ background: "#0e1a2e", borderRadius: 8, padding: 16, border: "1px solid #a855f733" }}>
          <div style={{ color: "#a855f7", fontSize: 12, fontWeight: 600, marginBottom: 10 }}>Trend Analysis (Last 6 Hours)</div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 60 }}>
            {[65, 72, 68, 88, 82, 78, 85, 88, 92, 86, 88, 84].map((v, i) => (
              <div key={i} style={{ flex: 1, height: `${(v / 100) * 60}px`, background: v > 85 ? "#f59e0b33" : "#a855f733", borderRadius: "2px 2px 0 0", position: "relative" }}>
                {i === 11 && <div style={{ position: "absolute", top: -14, left: "50%", transform: "translateX(-50%)", color: "#a855f7", fontSize: 8 }}>{v}</div>}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ color: "#445566", fontSize: 8 }}>-6h</span>
            <span style={{ color: "#445566", fontSize: 8 }}>-3h</span>
            <span style={{ color: "#445566", fontSize: 8 }}>Now</span>
          </div>
        </div>
      </div>
    );
  };

  const AgentView = () => (
    <div style={{ display: "flex", height: "calc(100% - 48px)" }}>
      <div style={{ width: 220, borderRight: "1px solid #1e3a5f", padding: 12, display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 28 }}>{selectedAgent.icon}</span>
          <div>
            <div style={{ color: selectedAgent.color, fontWeight: 600, fontSize: 13 }}>{selectedAgent.name}</div>
            <div style={{ color: "#667788", fontSize: 9 }}>SKILL.md loaded</div>
          </div>
        </div>
        <div style={{ color: "#667788", fontSize: 10, marginBottom: 6 }}>SKILLS</div>
        {selectedAgent.skills.map(s => (
          <button key={s} style={{ display: "block", width: "100%", padding: "7px 10px", marginBottom: 4, borderRadius: 5, border: `1px solid ${selectedAgent.color}22`, background: `${selectedAgent.color}08`, color: "#ccd6e0", fontSize: 10, cursor: "pointer", textAlign: "left" }}>
            {s}
          </button>
        ))}
        <div style={{ marginTop: "auto", padding: 8, background: "#0e1a2e", borderRadius: 6, border: "1px solid #1e3a5f" }}>
          <div style={{ color: "#667788", fontSize: 9, marginBottom: 4 }}>AGENT INFO</div>
          <div style={{ color: "#8899aa", fontSize: 9 }}>Queue: {selectedAgent.queue} items</div>
          <div style={{ color: "#8899aa", fontSize: 9 }}>Status: {selectedAgent.status}</div>
          <div style={{ color: "#8899aa", fontSize: 9 }}>Model: {selectedAgent.models_used ? selectedAgent.models_used[0] : "Claude"}</div>
        </div>
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, padding: 16, overflowY: "auto" }}>
          {chatMessages.map((m, i) => (
            <div key={i} style={{ marginBottom: 10, display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "75%", padding: "8px 12px", borderRadius: 8,
                background: m.role === "user" ? "#00b4d820" : m.role === "system" ? "#1a2f4a" : "#0e1a2e",
                border: `1px solid ${m.role === "user" ? "#00b4d833" : "#1e3a5f"}`,
                color: m.role === "system" ? "#667788" : "#ccd6e0", fontSize: 12
              }}>
                {m.role === "assistant" && <div style={{ color: selectedAgent.color, fontSize: 9, fontWeight: 600, marginBottom: 4 }}>{selectedAgent.name}</div>}
                {m.text}
                {m.streaming && <span style={{ color: "#667788" }}> ▊</span>}
              </div>
            </div>
          ))}
        </div>
        <div style={{ padding: 12, borderTop: "1px solid #1e3a5f", display: "flex", gap: 8 }}>
          <input value={inputText} onChange={e => setInputText(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder={`Message ${selectedAgent.name}...`}
            style={{ flex: 1, padding: "8px 12px", borderRadius: 6, border: "1px solid #1e3a5f", background: "#0a1628", color: "#e0e8f0", fontSize: 12, outline: "none" }} />
          <button onClick={handleSend} style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: selectedAgent.color, color: "#fff", fontSize: 11, fontWeight: 600, cursor: "pointer" }}>Send</button>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{ height: "100vh", background: "#0a1628", fontFamily: "'Inter', 'SF Pro', Arial, sans-serif", color: "#e0e8f0", overflow: "hidden" }}>
      <NavBar />
      <ErrorBanner />
      <div style={{ height: "calc(100vh - 48px)", overflowY: "auto" }}>
        {activeView === "dashboard" && <Dashboard />}
        {activeView === "triage" && <TriageView />}
        {activeView === "radiology" && <RadiologyView />}
        {activeView === "vitals" && <VitalsView />}
        {activeView === "agent" && selectedAgent && <AgentView />}
      </div>
    </div>
  );
}
