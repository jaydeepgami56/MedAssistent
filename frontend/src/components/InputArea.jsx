import { memo, useEffect } from "react";

const InputArea = memo(({ value, onChange, onSend, agentName, agentColor, textareaRef }) => {
  useEffect(() => {
    if (textareaRef && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  return (
    <div style={{
      padding: "12px 24px 16px",
      borderTop: "1px solid var(--border)",
      display: "flex", gap: 10, alignItems: "flex-end",
      background: "var(--bg-primary)",
    }}>
      <textarea
        dir="ltr"
        ref={textareaRef}
        value={value}
        onChange={onChange}
        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); } }}
        placeholder={`Message ${agentName}... (Shift+Enter for new line)`}
        style={{
          direction: "ltr",
          textAlign: "left",
          flex: 1,
          padding: "10px 14px",
          borderRadius: 10,
          border: "1px solid var(--input-border)",
          background: "var(--input-bg)",
          color: "var(--text-primary)",
          fontSize: 14,
          outline: "none",
          fontFamily: "'Inter', 'Space Grotesk', 'SF Pro Display', 'Segoe UI', sans-serif",
          resize: "none",
          overflowY: "auto",
          minHeight: "42px",
          maxHeight: "120px",
          transition: "border-color 0.15s",
          lineHeight: 1.5,
        }}
        onFocus={e => { e.target.style.borderColor = "var(--input-border-focus)"; }}
        onBlur={e => { e.target.style.borderColor = "var(--input-border)"; }}
      />
      <button
        onClick={onSend}
        style={{
          padding: "10px 18px",
          borderRadius: 10,
          border: "none",
          background: agentColor,
          color: "#fff",
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer",
          fontFamily: "'Inter', 'Space Grotesk', 'SF Pro Display', 'Segoe UI', sans-serif",
          transition: "opacity 0.15s",
          opacity: value.trim() ? 1 : 0.5,
        }}
      >
        Send
      </button>
    </div>
  );
});

export default InputArea;
