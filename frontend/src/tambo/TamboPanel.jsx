/**
 * TamboPanel — Right-side drawer panel with Tambo AI chat.
 * Floating button on bottom-right, expands to full-height right panel.
 * Uses Tambo hooks for thread management and message streaming.
 */
import { useState, useRef, useEffect } from "react";
import { useTamboThread, useTamboThreadInput } from "@tambo-ai/react";

const appFontStack = "'Inter', 'Space Grotesk', 'SF Pro Display', 'Segoe UI', sans-serif";
const headingFont = "'Space Grotesk', 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif";
const v = (name) => `var(${name})`;

const PANEL_WIDTH = 440;

function accentBg(hex, opacity = 0.07) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
}

// Suggestion chips for empty state
const SUGGESTIONS = [
  "patient vitals dashboard",
  "appointment booking form",
  "medication list",
  "sales by region chart",
  "staff schedule table",
];

export default function TamboPanel() {
  const [open, setOpen] = useState(false);
  const chatEndRef = useRef(null);
  const { thread } = useTamboThread();
  const { value, setValue, submit, isPending } = useTamboThreadInput();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [thread?.messages?.length, isPending]);

  const handleSubmit = () => {
    if (!value.trim() || isPending) return;
    submit();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // ── Collapsed: floating button ───────────────────────────
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 1000,
          width: 56, height: 56, borderRadius: "50%",
          background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
          border: "none",
          boxShadow: "0 4px 20px rgba(99,102,241,0.4)",
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 24, color: "#fff",
          transition: "transform 0.2s, box-shadow 0.2s",
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = "scale(1.08)"; e.currentTarget.style.boxShadow = "0 6px 28px rgba(99,102,241,0.55)"; }}
        onMouseLeave={e => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.4)"; }}
        title="Tambo AI"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18" />
          <path d="M9 21V9" />
        </svg>
      </button>
    );
  }

  // ── Expanded: full-height right panel ───────────────────
  const messages = thread?.messages || [];
  const hasMessages = messages.length > 0;

  return (
    <>
      {/* Backdrop overlay */}
      <div
        onClick={() => setOpen(false)}
        style={{
          position: "fixed", inset: 0, zIndex: 999,
          background: "rgba(0,0,0,0.2)",
          transition: "opacity 0.2s",
        }}
      />

      {/* Panel */}
      <div style={{
        position: "fixed", top: 0, right: 0, bottom: 0, zIndex: 1000,
        width: PANEL_WIDTH,
        background: v("--bg-primary"),
        borderLeft: `1px solid ${v("--border")}`,
        boxShadow: "-8px 0 40px rgba(0,0,0,0.15)",
        display: "flex", flexDirection: "column",
        fontFamily: appFontStack,
        animation: "tamboSlideIn 0.25s ease-out",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "16px 20px",
          borderBottom: `1px solid ${v("--border")}`,
          background: v("--bg-secondary"),
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M3 9h18" />
                <path d="M9 21V9" />
              </svg>
            </div>
            <div>
              <div style={{ color: v("--text-primary"), fontWeight: 700, fontSize: 15, fontFamily: headingFont }}>Tambo AI</div>
              <div style={{ color: v("--text-muted"), fontSize: 10 }}>Generative UI Agent</div>
            </div>
          </div>
          <button
            onClick={() => setOpen(false)}
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

        {/* Messages area */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
          {!hasMessages && !isPending && (
            <div style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", height: "100%", textAlign: "center",
              padding: "0 20px",
            }}>
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 16,
              }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <path d="M3 9h18" />
                  <path d="M9 21V9" />
                </svg>
              </div>
              <div style={{ color: v("--text-primary"), fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
                Tambo Generative UI
              </div>
              <div style={{ color: v("--text-muted"), fontSize: 13, lineHeight: 1.6, maxWidth: 300, marginBottom: 20 }}>
                Describe any UI and Tambo will pick the right component and generate it. Try a suggestion below.
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "center" }}>
                {SUGGESTIONS.map(s => (
                  <button key={s}
                    onClick={() => { setValue(s); }}
                    style={{
                      padding: "6px 12px", borderRadius: 16,
                      border: `1px solid ${v("--border")}`, background: "transparent",
                      color: v("--text-secondary"), fontSize: 12, cursor: "pointer",
                      fontFamily: appFontStack,
                      transition: "border-color 0.15s, color 0.15s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.color = "#8b5cf6"; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = v("--border"); e.currentTarget.style.color = v("--text-secondary"); }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => {
            const isUser = message.role === "user";
            const isAssistant = message.role === "assistant";

            // Extract text parts
            const textParts = Array.isArray(message.content)
              ? message.content.filter(p => p.type === "text").map(p => p.text).join("\n")
              : typeof message.content === "string" ? message.content : "";

            return (
              <div key={message.id} style={{ marginBottom: 16 }}>
                {isUser && (
                  <div style={{ display: "flex", justifyContent: "flex-end" }}>
                    <div style={{
                      maxWidth: "85%", padding: "10px 14px", borderRadius: "14px 14px 4px 14px",
                      background: v("--user-msg-bg"), color: v("--user-msg-text"),
                      fontSize: 13, lineHeight: 1.5,
                    }}>
                      {textParts}
                    </div>
                  </div>
                )}

                {isAssistant && (
                  <div>
                    <div style={{ color: "#8b5cf6", fontSize: 10, fontWeight: 600, marginBottom: 6, fontFamily: headingFont }}>
                      Tambo AI
                    </div>
                    {textParts && (
                      <div style={{
                        color: v("--text-primary"), fontSize: 13, lineHeight: 1.6, marginBottom: 8,
                      }}>
                        {textParts}
                      </div>
                    )}
                    {/* Rendered Tambo component */}
                    {message.renderedComponent && (
                      <div style={{ marginTop: 8 }}>
                        {message.renderedComponent}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading indicator */}
          {isPending && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ color: "#8b5cf6", fontSize: 10, fontWeight: 600, marginBottom: 6, fontFamily: headingFont }}>
                Tambo AI <span style={{ color: v("--text-muted"), fontWeight: 400 }}>is generating...</span>
              </div>
              <div style={{
                padding: 20, borderRadius: 12,
                border: `1px solid ${v("--border")}`,
                background: v("--card-bg"),
              }}>
                {[45, 70, 30].map((w, i) => (
                  <div key={i} style={{
                    width: `${w}%`, height: i === 0 ? 18 : 12, borderRadius: 6, marginBottom: i < 2 ? 10 : 0,
                    background: `linear-gradient(90deg, ${v("--bg-tertiary")} 25%, ${v("--border")} 50%, ${v("--bg-tertiary")} 75%)`,
                    backgroundSize: "800px 100%",
                    animation: "shimmer 1.5s infinite linear",
                  }} />
                ))}
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input area */}
        <div style={{
          padding: "14px 20px",
          borderTop: `1px solid ${v("--border")}`,
          background: v("--bg-secondary"),
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
            <textarea
              dir="ltr"
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe a UI component..."
              rows={1}
              style={{
                flex: 1, padding: "10px 14px", borderRadius: 12,
                border: `1px solid ${v("--input-border")}`, background: v("--input-bg"),
                color: v("--text-primary"), fontSize: 13, fontFamily: appFontStack,
                resize: "none", outline: "none", lineHeight: 1.4, maxHeight: 100,
              }}
              onFocus={e => e.currentTarget.style.borderColor = "#8b5cf6"}
              onBlur={e => e.currentTarget.style.borderColor = v("--input-border")}
            />
            <button
              onClick={handleSubmit}
              disabled={!value.trim() || isPending}
              style={{
                width: 40, height: 40, borderRadius: 12, flexShrink: 0,
                border: "none",
                background: (value.trim() && !isPending) ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : v("--bg-tertiary"),
                color: (value.trim() && !isPending) ? "#fff" : v("--text-muted"),
                fontSize: 16, cursor: (value.trim() && !isPending) ? "pointer" : "not-allowed",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.2s",
              }}
            >
              {isPending ? (
                <span style={{ fontSize: 14, animation: "spin 1s linear infinite" }}>⟳</span>
              ) : "↑"}
            </button>
          </div>
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            marginTop: 8,
          }}>
            <span style={{ color: v("--text-muted"), fontSize: 10 }}>
              Powered by Tambo AI
            </span>
            <span style={{ color: v("--text-muted"), fontSize: 10 }}>
              {messages.length} message{messages.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>

      {/* Animation keyframes */}
      <style>{`
        @keyframes tamboSlideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
