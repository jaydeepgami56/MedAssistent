/**
 * Tambo component registrations with Zod schemas.
 * These components are registered with TamboProvider so the AI agent
 * can dynamically select and render them based on user messages.
 */
import { z } from "zod";

const v = (name) => `var(${name})`;
const appFontStack = "'Inter', 'Space Grotesk', 'SF Pro Display', 'Segoe UI', sans-serif";
const headingFont = "'Space Grotesk', 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif";

function accentBg(hex, opacity = 0.07) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${opacity})`;
}

const cardStyle = {
  background: v("--card-bg"),
  borderRadius: 12,
  border: `1px solid ${v("--border")}`,
  boxShadow: v("--card-shadow"),
};

// ── StatsCard ──────────────────────────────────────────────────
function StatsCard({ title, description, items = [] }) {
  const accent = items[0]?.color || "#8b5cf6";
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accent}`, fontFamily: appFontStack }}>
      <div style={{ color: accent, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
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
}

// ── InfoCard ───────────────────────────────────────────────────
function InfoCard({ title, description, items = [], accentColor = "#3b82f6", layout = "grid" }) {
  const isGrid = layout === "grid";
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accentColor}`, fontFamily: appFontStack }}>
      <div style={{ color: accentColor, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
      <div style={{ display: "grid", gridTemplateColumns: isGrid ? "repeat(auto-fill, minmax(160px, 1fr))" : "1fr", gap: 10 }}>
        {items.map((item, i) => (
          <div key={i} style={{ ...cardStyle, padding: 14, borderLeft: `3px solid ${item.color || accentColor}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {item.icon && <span style={{ fontSize: 22 }}>{item.icon}</span>}
              <div>
                <div style={{ color: v("--text-muted"), fontSize: 10 }}>{item.label}</div>
                <div style={{ color: item.color || accentColor, fontSize: 18, fontWeight: 700 }}>{item.value}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── DataTable ──────────────────────────────────────────────────
function DataTable({ title, description, columns = [], rows = [], accentColor = "#22c55e" }) {
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accentColor}`, overflow: "auto", fontFamily: appFontStack }}>
      <div style={{ color: accentColor, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key} style={{
                textAlign: "left", padding: "8px 12px",
                borderBottom: `2px solid ${accentColor}`,
                color: accentColor, fontWeight: 600, fontSize: 11, textTransform: "uppercase",
              }}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map(col => (
                <td key={col.key} style={{
                  padding: "8px 12px",
                  borderBottom: `1px solid ${v("--border")}`,
                  color: v("--text-primary"),
                }}>{row[col.key] ?? "—"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── FormPanel ──────────────────────────────────────────────────
function FormPanel({ title, description, fields = [], accentColor = "#f59e0b", submitLabel = "Submit" }) {
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accentColor}`, fontFamily: appFontStack }}>
      <div style={{ color: accentColor, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {fields.map((f, i) => (
          <div key={i}>
            <label style={{ display: "block", color: v("--text-secondary"), fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{f.label}</label>
            {f.type === "textarea" ? (
              <textarea style={{
                width: "100%", padding: 10, borderRadius: 6,
                border: `1px solid ${v("--border")}`, background: v("--input-bg"),
                color: v("--text-primary"), fontSize: 13, fontFamily: appFontStack, minHeight: 60,
              }} placeholder={f.placeholder || f.label} />
            ) : f.type === "select" ? (
              <select style={{
                width: "100%", padding: 10, borderRadius: 6,
                border: `1px solid ${v("--border")}`, background: v("--input-bg"),
                color: v("--text-primary"), fontSize: 13,
              }}>
                {(f.options || []).map((opt, j) => <option key={j} value={opt}>{opt}</option>)}
              </select>
            ) : (
              <input type={f.type || "text"} style={{
                width: "100%", padding: 10, borderRadius: 6,
                border: `1px solid ${v("--border")}`, background: v("--input-bg"),
                color: v("--text-primary"), fontSize: 13,
              }} placeholder={f.placeholder || f.label} />
            )}
          </div>
        ))}
        <button style={{
          padding: "10px 20px", borderRadius: 6, border: "none",
          background: accentColor, color: "#fff",
          fontSize: 13, fontWeight: 600, cursor: "pointer", alignSelf: "flex-start",
        }}>{submitLabel}</button>
      </div>
    </div>
  );
}

// ── InfoList ───────────────────────────────────────────────────
function InfoList({ title, description, items = [], accentColor = "#a855f7" }) {
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accentColor}`, fontFamily: appFontStack }}>
      <div style={{ color: accentColor, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {items.map((item, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "10px 12px", borderRadius: 8,
            background: v("--bg-secondary"), border: `1px solid ${v("--border")}`,
          }}>
            {item.icon && <span style={{ fontSize: 20 }}>{item.icon}</span>}
            <div style={{ flex: 1 }}>
              <div style={{ color: v("--text-primary"), fontSize: 13, fontWeight: 600 }}>{item.label || item.name}</div>
              {item.value && <div style={{ color: v("--text-muted"), fontSize: 11 }}>{item.value}</div>}
            </div>
            {item.status && (
              <span style={{
                fontSize: 10, padding: "2px 8px", borderRadius: 10,
                background: accentBg(accentColor, 0.1), color: accentColor,
              }}>{item.status}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── BarChart (simple) ──────────────────────────────────────────
function BarChart({ title, description, data = [], accentColor = "#00b4d8" }) {
  const maxVal = Math.max(...data.map(d => d.value), 1);
  return (
    <div style={{ ...cardStyle, padding: 20, borderLeft: `3px solid ${accentColor}`, fontFamily: appFontStack }}>
      <div style={{ color: accentColor, fontSize: 16, fontWeight: 700, marginBottom: 4, fontFamily: headingFont }}>{title}</div>
      {description && <div style={{ color: v("--text-secondary"), fontSize: 12, marginBottom: 14 }}>{description}</div>}
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {data.map((d, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 80, color: v("--text-secondary"), fontSize: 12, textAlign: "right", flexShrink: 0 }}>{d.name}</div>
            <div style={{ flex: 1, height: 24, background: v("--bg-tertiary"), borderRadius: 4, overflow: "hidden" }}>
              <div style={{
                width: `${(d.value / maxVal) * 100}%`, height: "100%",
                background: d.color || accentColor, borderRadius: 4,
                transition: "width 0.3s ease",
                display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 6,
              }}>
                <span style={{ color: "#fff", fontSize: 10, fontWeight: 600 }}>{d.value}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Zod Schemas & Component Registration ───────────────────────

const itemSchema = z.object({
  label: z.string().describe("Display label for this item"),
  value: z.string().describe("The value to display"),
  icon: z.string().optional().describe("Emoji icon"),
  color: z.string().optional().describe("Hex color like #ef4444"),
});

const listItemSchema = z.object({
  label: z.string().optional().describe("Primary text"),
  name: z.string().optional().describe("Alternative to label"),
  value: z.string().optional().describe("Secondary text"),
  icon: z.string().optional().describe("Emoji icon"),
  status: z.string().optional().describe("Status badge text"),
});

const columnSchema = z.object({
  key: z.string().describe("Data key matching row object keys"),
  label: z.string().describe("Column header label"),
});

const fieldSchema = z.object({
  name: z.string().describe("Field name"),
  label: z.string().describe("Display label"),
  type: z.enum(["text", "number", "email", "date", "textarea", "select"]).optional().describe("Input type"),
  placeholder: z.string().optional().describe("Placeholder text"),
  options: z.array(z.string()).optional().describe("Options for select type"),
});

const chartDataSchema = z.object({
  name: z.string().describe("Label for this data point"),
  value: z.number().describe("Numeric value"),
  color: z.string().optional().describe("Bar color override"),
});

export const tamboComponents = [
  {
    name: "StatsCard",
    description: "A statistics grid showing multiple metrics/KPIs with icons and values. Best for dashboards, vitals, summaries. Use when user asks for stats, metrics, vitals, KPIs, or status overview.",
    component: StatsCard,
    propsSchema: z.object({
      title: z.string().describe("Card title"),
      description: z.string().optional().describe("Brief subtitle"),
      items: z.array(itemSchema).describe("Array of stat items to display"),
    }),
  },
  {
    name: "InfoCard",
    description: "An information card displaying labeled data items in a grid or list layout. Good for weather, details, summaries, profiles. Use when user asks for info, details, or summary cards.",
    component: InfoCard,
    propsSchema: z.object({
      title: z.string().describe("Card title"),
      description: z.string().optional().describe("Brief subtitle"),
      items: z.array(itemSchema).describe("Array of info items"),
      accentColor: z.string().optional().describe("Accent hex color"),
      layout: z.enum(["grid", "list"]).optional().describe("Layout style"),
    }),
  },
  {
    name: "DataTable",
    description: "A data table with headers and rows. Best for patient lists, records, inventories, schedules, comparison data. Use when user asks for a table, list of records, or structured data.",
    component: DataTable,
    propsSchema: z.object({
      title: z.string().describe("Table title"),
      description: z.string().optional().describe("Brief subtitle"),
      columns: z.array(columnSchema).describe("Table column definitions"),
      rows: z.array(z.record(z.string())).describe("Array of row objects with keys matching columns"),
      accentColor: z.string().optional().describe("Accent hex color"),
    }),
  },
  {
    name: "FormPanel",
    description: "An interactive form with various input fields. Best for registration, data entry, appointment booking, surveys. Use when user asks for a form, input, or data entry UI.",
    component: FormPanel,
    propsSchema: z.object({
      title: z.string().describe("Form title"),
      description: z.string().optional().describe("Brief subtitle"),
      fields: z.array(fieldSchema).describe("Form field definitions"),
      accentColor: z.string().optional().describe("Accent hex color"),
      submitLabel: z.string().optional().describe("Submit button text"),
    }),
  },
  {
    name: "InfoList",
    description: "A styled list of items with optional icons and status badges. Best for medication lists, task lists, notifications, activity feeds. Use when user asks for a list.",
    component: InfoList,
    propsSchema: z.object({
      title: z.string().describe("List title"),
      description: z.string().optional().describe("Brief subtitle"),
      items: z.array(listItemSchema).describe("List items"),
      accentColor: z.string().optional().describe("Accent hex color"),
    }),
  },
  {
    name: "BarChart",
    description: "A horizontal bar chart for comparing values. Best for sales, performance, rankings, distribution data. Use when user asks for a chart, graph, or data visualization.",
    component: BarChart,
    propsSchema: z.object({
      title: z.string().describe("Chart title"),
      description: z.string().optional().describe("Brief subtitle"),
      data: z.array(chartDataSchema).describe("Chart data points"),
      accentColor: z.string().optional().describe("Default bar color"),
    }),
  },
];
