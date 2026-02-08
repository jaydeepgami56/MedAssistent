import { useState } from "react";

const agents = [
  { id: "triage", name: "Triage Agent", icon: "🚨", color: "#ef4444", bg: "#1a0505", skills: ["ESI Scoring", "Red Flag Detection", "Patient Routing", "Emergency Alert"], status: "Active", queue: 12 },
  { id: "radiology", name: "Radiology Agent", icon: "🩻", color: "#00b4d8", bg: "#051a1f", skills: ["X-Ray Analysis", "MRI Interpretation", "CT Review", "Report Generation"], status: "Active", queue: 5 },
  { id: "diagnostic", name: "Diagnostic Agent", icon: "🔬", color: "#22c55e", bg: "#051a0a", skills: ["Differential Dx", "Test Recommendation", "Pattern Recognition", "Rare Disease"], status: "Active", queue: 8 },
  { id: "pharmacy", name: "Pharmacy Agent", icon: "💊", color: "#f59e0b", bg: "#1a1405", skills: ["Drug Interactions", "Dosage Calc", "Contraindications", "Med Reconciliation"], status: "Active", queue: 3 },
  { id: "monitoring", name: "Monitoring Agent", icon: "📊", color: "#a855f7", bg: "#0f051a", skills: ["Vital Tracking", "MEWS Score", "Anomaly Detection", "Alert System"], status: "Active", queue: 24 },
  { id: "docs", name: "Documentation Agent", icon: "📋", color: "#06b6d4", bg: "#051519", skills: ["SOAP Notes", "Discharge Summary", "ICD-10 Coding", "Referral Letter"], status: "Active", queue: 7 },
  { id: "research", name: "Research Agent", icon: "📚", color: "#10b981", bg: "#051a12", skills: ["PubMed Search", "Guideline Lookup", "Trial Matching", "Evidence Synthesis"], status: "Idle", queue: 0 },
  { id: "coordinator", name: "Coordinator Agent", icon: "🧠", color: "#e879f9", bg: "#19051a", skills: ["Agent Routing", "Consensus Build", "Safety Check", "Escalation"], status: "Active", queue: 0 }
];

const triagePatients = [
  { id: 1, name: "Patient A — 67F", complaint: "Chest pain, shortness of breath", esi: 1, color: "#ef4444", label: "Resuscitation", time: "0 min" },
  { id: 2, name: "Patient B — 45M", complaint: "Stroke symptoms (FAST positive)", esi: 2, color: "#f97316", label: "Emergency", time: "< 10 min" },
  { id: 3, name: "Patient C — 32F", complaint: "Abdominal pain, fever 39.2°C", esi: 3, color: "#eab308", label: "Urgent", time: "30 min" },
  { id: 4, name: "Patient D — 28M", complaint: "Ankle sprain, moderate swelling", esi: 4, color: "#22c55e", label: "Semi-urgent", time: "60 min" },
  { id: 5, name: "Patient E — 55F", complaint: "Prescription refill request", esi: 5, color: "#3b82f6", label: "Non-urgent", time: "120 min" },
];

const radiologyReport = {
  patient: "Patient B — 45M",
  modality: "Chest X-Ray (PA)",
  findings: [
    { text: "Bilateral infiltrates in lower lobes", confidence: 0.94, severity: "high" },
    { text: "Mild cardiomegaly noted", confidence: 0.87, severity: "moderate" },
    { text: "No pneumothorax identified", confidence: 0.96, severity: "normal" },
    { text: "Costophrenic angles blunted bilaterally", confidence: 0.82, severity: "moderate" },
  ],
  similarCases: 4,
  recommendation: "Correlate with CT for further evaluation. Suggest cardiology consult."
};

const vitals = { hr: 88, bp: "132/84", spo2: 97, temp: 37.1, rr: 18, mews: 2 };

export default function MedAssistDashboard() {
  const [activeView, setActiveView] = useState("dashboard");
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [inputText, setInputText] = useState("");

  const handleAgentClick = (agent) => {
    setSelectedAgent(agent);
    setActiveView("agent");
    setChatMessages([
      { role: "system", text: `${agent.name} activated. Ready to assist.` },
      { role: "assistant", text: `Hello! I'm the ${agent.name}. How can I help you today? My available skills are: ${agent.skills.join(", ")}.` }
    ]);
  };

  const handleSend = () => {
    if (!inputText.trim()) return;
    setChatMessages(prev => [...prev, { role: "user", text: inputText }]);
    setTimeout(() => {
      setChatMessages(prev => [...prev, {
        role: "assistant",
        text: `Processing your request with ${selectedAgent.name}... [AI-assisted analysis — requires clinician verification]`
      }]);
    }, 500);
    setInputText("");
  };

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
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 6px #22c55e" }} />
        <span style={{ color: "#667788", fontSize: 11 }}>7 Agents Online</span>
      </div>
    </div>
  );

  const Dashboard = () => (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ color: "#e0e8f0", margin: 0, fontSize: 18 }}>Agent Control Center</h2>
          <p style={{ color: "#667788", margin: "4px 0 0", fontSize: 12 }}>8 specialized medical agents powered by OpenClaw</p>
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          {[{ label: "Active Agents", val: "7/8", color: "#22c55e" }, { label: "Queue Total", val: "59", color: "#f59e0b" }, { label: "ESI-1 Alerts", val: "1", color: "#ef4444" }].map(s => (
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
              {a.skills.map(s => (
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

  const TriageView = () => (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: "#ef4444", margin: 0, fontSize: 18 }}>🚨 Triage Dashboard</h2>
        <div style={{ display: "flex", gap: 8 }}>
          {[{ esi: "ESI-1", count: 1, color: "#ef4444" }, { esi: "ESI-2", count: 2, color: "#f97316" }, { esi: "ESI-3", count: 4, color: "#eab308" }, { esi: "ESI-4", count: 3, color: "#22c55e" }, { esi: "ESI-5", count: 2, color: "#3b82f6" }].map(e => (
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

  const RadiologyView = () => (
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
              {[1, 2, 3, 4].map(n => (
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

  const VitalsView = () => (
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
          <div style={{ color: "#8899aa", fontSize: 9 }}>Model: Claude + Specialist</div>
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
