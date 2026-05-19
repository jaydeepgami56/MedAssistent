import { useState, useMemo, useEffect, useRef } from "react";

/* ─────────────────────────────────────────────
   FEEDBACK APPLIED (from Clinical UX Review)
   ─────────────────────────────────────────────
   SAFETY-1  Two-step order signing: "Accept & sign" opens inline confirm
             panel listing every checked order; separate "Confirm & submit"
             required. Orders default UN-checked; clinician selects actively.
   SAFETY-2  Three-tier pharmacy alert severity:
             • Advisory  → small pill (unchanged)
             • Warning   → inline callout with amber left-border
             • Critical Hold → full-width red banner + mandatory acknowledge
             "Accept & sign" disabled when unacknowledged Critical Holds exist.
   SAFETY-3  Live data-freshness timestamps: every panel shows "N min ago"
             relative to a live clock; panels >5 min get a yellow stale border
             and warning label. Empty/error/pending states added throughout.
   UX-1      Vitals card shows both SBP and DBP values (not "(SBP)" label).
   UX-2      AI badge font bumped to 11px; tooltip on hover explains confidence
             methodology ("model posterior probability against 12,408 cases").
   UX-3      DDx confidence bars: tooltip explaining what % means.
   UX-4      Radiology approval requires a confirmation step before persisting.
   UX-5      Canvas page moved after a separator — visually distinct from
             active patient-care routes.
   ───────────────────────────────────────────── */

const css = `
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500;600&display=swap');

  .ma { --bg:#faf8f4;--surface:#ffffff;--surface-2:#f4f1ea;--ink:#0e1116;--ink-2:#2b3038;--muted:#6b7280;--muted-2:#9aa1ad;--line:#e7e2d6;--line-2:#d8d2c2;--accent:#155e75;--accent-soft:#ecf6f8;--accent-ink:#0c4a5e;--critical:#b91c1c;--critical-soft:#fdecec;--warn:#b45309;--warn-soft:#fdf2e3;--ok:#166534;--ok-soft:#ecf6ed;--info:#1e40af;--info-soft:#eaf0fb;--r:6px;--rl:10px; font-family:'IBM Plex Sans',system-ui,sans-serif;font-size:14px;line-height:1.45;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;height:620px;display:flex;overflow:hidden; }
  .ma.dark { --bg:#0d1014;--surface:#14181e;--surface-2:#1a1f26;--ink:#f1ede2;--ink-2:#cdd1d8;--muted:#8b929c;--muted-2:#5e6671;--line:#232a32;--line-2:#2c343e;--accent:#67e8f9;--accent-soft:#0d2a30;--accent-ink:#a5f3fc;--critical:#f87171;--critical-soft:#2a1414;--warn:#fbbf24;--warn-soft:#2a2010;--ok:#4ade80;--ok-soft:#11251a;--info:#93c5fd;--info-soft:#11203a; }
  .ma * { box-sizing:border-box; }
  .mono { font-family:'IBM Plex Mono',monospace; }
  .serif { font-family:'IBM Plex Serif',Georgia,serif; }

  /* ── Sidebar ── */
  .ma-sb { width:216px;flex-shrink:0;border-right:1px solid var(--line);background:var(--surface);display:flex;flex-direction:column;padding:16px 12px;gap:18px;overflow-y:auto; }
  .ma-brand { display:flex;align-items:center;gap:10px;padding:2px 6px; }
  .ma-mark { width:24px;height:24px;border-radius:5px;background:var(--ink);display:grid;place-items:center;color:var(--bg);font-weight:700;font-size:12px; }
  .ma-brand-name { font-weight:600;font-size:13px;letter-spacing:-0.01em; }
  .ma-brand-name small { display:block;color:var(--muted);font-weight:400;font-size:10px; }
  .ma-nav-group { display:flex;flex-direction:column;gap:1px; }
  .ma-nav-lbl { margin:0 6px 5px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted-2); }
  .ma-nav-sep { height:1px;background:var(--line);margin:8px 0; }
  .ma-ni { display:flex;align-items:center;gap:9px;padding:6px 8px;border-radius:5px;color:var(--ink-2);font-size:12.5px;cursor:pointer;border:1px solid transparent;user-select:none; }
  .ma-ni:hover { background:var(--surface-2); }
  .ma-ni.active { background:var(--surface-2);color:var(--ink);border-color:var(--line-2);font-weight:500; }
  .ma-ni .ico { width:13px;height:13px;flex:0 0 13px;color:var(--muted); }
  .ma-ni.active .ico { color:var(--accent-ink); }
  .ma-ni .bdg { margin-left:auto;font-size:10px;font-family:'IBM Plex Mono',monospace;color:var(--muted); }
  .ma-ni.active .bdg { color:var(--ink); }
  .ma-ctx { border:1px solid var(--line);border-radius:var(--r);padding:9px;background:var(--surface);display:flex;flex-direction:column;gap:5px;margin-top:auto; }
  .ma-ctx-row { display:flex;justify-content:space-between;font-size:11px;color:var(--muted); }
  .ma-ctx-row strong { color:var(--ink);font-weight:500; }
  .pulse { display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--ok); }
  .pdot { width:6px;height:6px;border-radius:50%;background:currentColor;animation:mapulse 2.4s infinite; }
  @keyframes mapulse { 0%{box-shadow:0 0 0 0 rgba(22,101,52,.4)} 70%{box-shadow:0 0 0 7px rgba(22,101,52,0)} 100%{box-shadow:0 0 0 0 rgba(22,101,52,0)} }

  /* ── Main ── */
  .ma-main { display:flex;flex-direction:column;flex:1;min-width:0; }
  .ma-topbar { display:flex;align-items:center;gap:12px;padding:10px 20px;border-bottom:1px solid var(--line);background:var(--surface);flex-shrink:0; }
  .ma-crumbs { font-size:12.5px;color:var(--muted);display:flex;gap:5px;align-items:baseline; }
  .ma-crumbs strong { color:var(--ink);font-weight:500; }
  .ma-top-right { margin-left:auto;display:flex;gap:7px;align-items:center; }
  .ma-search { display:flex;align-items:center;gap:7px;padding:5px 9px;border:1px solid var(--line);border-radius:var(--r);background:var(--bg);color:var(--muted);font-size:12px;min-width:200px; }
  .ma-search kbd { margin-left:auto;font-family:'IBM Plex Mono',monospace;font-size:10px;padding:1px 4px;border:1px solid var(--line);border-bottom-width:2px;border-radius:3px; }
  .icobtn { width:28px;height:28px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);display:grid;place-items:center;color:var(--ink-2);cursor:pointer; }
  .icobtn:hover { background:var(--surface-2); }
  .ma-content { flex:1;min-height:0;overflow-y:auto;background:var(--bg); }

  /* ── Page head ── */
  .ph { padding:20px 26px 14px;display:grid;grid-template-columns:1fr auto;gap:20px;align-items:end;border-bottom:1px solid var(--line); }
  .ph h1 { font-family:'IBM Plex Serif',serif;font-weight:500;font-size:22px;letter-spacing:-0.015em;margin:0 0 3px; }
  .ph-sub { color:var(--muted);font-size:12px;max-width:60ch; }
  .stat-row { display:flex;border:1px solid var(--line);border-radius:var(--r);overflow:hidden;background:var(--surface); }
  .stat { padding:7px 13px;border-right:1px solid var(--line);min-width:76px; }
  .stat:last-child { border-right:0; }
  .stat .k { font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:2px; }
  .stat .v { font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:500;color:var(--ink); }
  .stat .v.crit { color:var(--critical); } .stat .v.warn { color:var(--warn); } .stat .v.ok { color:var(--ok); }

  /* ── Banners ── */
  .banner { display:flex;align-items:center;gap:9px;padding:7px 14px;font-size:11.5px;background:var(--warn-soft);color:var(--warn);border-bottom:1px solid var(--line);font-family:'IBM Plex Mono',monospace; }
  .banner.info { background:var(--accent-soft);color:var(--accent-ink); }
  .banner.crit { background:var(--critical-soft);color:var(--critical); }

  /* ── Freshness indicator ── */
  .fresh { display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-family:'IBM Plex Mono',monospace;padding:2px 6px;border-radius:3px;background:var(--ok-soft);color:var(--ok); }
  .fresh.stale { background:var(--warn-soft);color:var(--warn); }
  .fresh.old { background:var(--critical-soft);color:var(--critical); }
  .stale-panel { border:1.5px solid var(--warn) !important; }

  /* ── Triage queue ── */
  .queue { display:grid;grid-template-columns:1.35fr 1fr;height:100%; }
  .qlist { border-right:1px solid var(--line);overflow-y:auto;background:var(--surface); }
  .qtoolbar { display:flex;align-items:center;gap:7px;padding:9px 14px;border-bottom:1px solid var(--line);background:var(--surface-2);position:sticky;top:0;z-index:2; }
  .qfil { display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;font-size:11.5px;cursor:pointer;border:1px solid var(--line-2);background:var(--surface);color:var(--ink-2); }
  .qfil[aria-pressed="true"] { background:var(--ink);color:var(--bg);border-color:var(--ink); }
  .prow { display:grid;grid-template-columns:5px 32px 1fr auto auto;gap:12px;padding:12px 14px;border-bottom:1px solid var(--line);cursor:pointer;align-items:center; }
  .prow:hover { background:var(--surface-2); }
  .prow.sel { background:var(--accent-soft); }
  .esib { width:4px;height:32px;border-radius:2px; }
  .e1{background:var(--critical)} .e2{background:#ea580c} .e3{background:var(--warn)} .e4{background:var(--ok)} .e5{background:#1e3a8a}
  .pid { width:32px;height:32px;border-radius:50%;background:var(--surface-2);border:1px solid var(--line);display:grid;place-items:center;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-2); }
  .epill { font-family:'IBM Plex Mono',monospace;font-size:10.5px;font-weight:600;padding:2px 5px;border-radius:3px;border:1px solid; }
  .ep1{color:var(--critical);border-color:var(--critical);background:var(--critical-soft)} .ep2{color:#ea580c;border-color:#ea580c;background:#fef3ed} .ep3{color:var(--warn);border-color:var(--warn);background:var(--warn-soft)} .ep4{color:var(--ok);border-color:var(--ok);background:var(--ok-soft)} .ep5{color:var(--info);border-color:var(--info);background:var(--info-soft)}
  .pname { font-weight:500;font-size:13px; }
  .pchief { color:var(--ink-2);font-size:12.5px;margin-top:3px; }
  .pwait { text-align:right;font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--muted); }
  .pwait.over { color:var(--critical); }

  /* ── Patient detail ── */
  .det { overflow-y:auto; }
  .det-head { padding:16px 20px;border-bottom:1px solid var(--line);background:var(--surface);display:flex;flex-direction:column;gap:10px; }
  .det-name { font-family:'IBM Plex Serif',serif;font-size:19px;font-weight:500; }
  .det-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r);overflow:hidden; }
  .det-grid > div { background:var(--surface);padding:8px 10px; }
  .kv .k { font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:2px; }
  .kv .v { font-family:'IBM Plex Mono',monospace;font-size:12.5px;color:var(--ink); }
  .kv .v.crit { color:var(--critical); } .kv .v.warn { color:var(--warn); }
  .det-sec { padding:13px 20px;border-bottom:1px solid var(--line); }
  .det-sec h3 { font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:0 0 9px;font-weight:600;display:flex;align-items:center;gap:7px;flex-wrap:wrap; }

  /* AI badge — bigger, tooltip-enabled */
  .ai-bdg { position:relative;font-family:'IBM Plex Mono',monospace;font-size:11px;padding:2px 6px;border:1px solid var(--accent);color:var(--accent-ink);border-radius:2px;background:var(--accent-soft);cursor:help; }
  .ai-bdg:hover .ai-tip { display:block; }
  .ai-tip { display:none;position:absolute;top:calc(100% + 6px);left:0;width:230px;background:var(--ink);color:var(--bg);font-size:11px;padding:8px 10px;border-radius:5px;line-height:1.5;z-index:99;font-family:'IBM Plex Sans',sans-serif;font-weight:400;letter-spacing:0;text-transform:none;white-space:normal; }

  /* DDx */
  .ddx { display:flex;flex-direction:column;gap:5px; }
  .ddx-row { display:grid;grid-template-columns:1fr 52px 72px;gap:10px;align-items:center;padding:7px 9px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface); }
  .bar { height:4px;background:var(--surface-2);border-radius:2px;overflow:hidden; }
  .bar span { display:block;height:100%; }

  /* ── SAFETY-1: Order signing — two-step ── */
  .orders-list { display:flex;flex-direction:column;gap:5px; }
  .order-item { display:flex;align-items:center;gap:9px;padding:7px 9px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);cursor:pointer;transition:border-color .15s; }
  .order-item:hover { border-color:var(--line-2); }
  .order-item input[type=checkbox] { accent-color:var(--accent);width:14px;height:14px;flex-shrink:0;cursor:pointer; }
  .sign-confirm-box { margin:12px 20px;border:1.5px solid var(--accent);border-radius:var(--rl);background:var(--accent-soft);overflow:hidden; }
  .sign-confirm-hd { padding:10px 14px;border-bottom:1px solid var(--accent);display:flex;align-items:center;justify-content:space-between; }
  .sign-confirm-hd h4 { margin:0;font-size:13px;font-weight:600;color:var(--accent-ink); }
  .sign-confirm-body { padding:10px 14px;display:flex;flex-direction:column;gap:5px; }
  .sign-order-line { display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--ink); }
  .sign-confirm-footer { padding:10px 14px;border-top:1px solid var(--accent);display:flex;gap:8px;align-items:center; }
  .sign-done { margin:12px 20px 18px;padding:10px 14px;border:1px solid var(--ok);border-radius:var(--r);background:var(--ok-soft);color:var(--ok);font-size:12.5px;display:flex;align-items:center;gap:8px;font-family:'IBM Plex Mono',monospace; }

  /* Actions bar */
  .act-bar { display:flex;gap:7px;padding:12px 20px 16px;align-items:center; }
  .btn { padding:7px 13px;border-radius:var(--r);border:1px solid var(--line-2);background:var(--surface);color:var(--ink);font-size:12.5px;font-family:inherit;cursor:pointer;display:inline-flex;align-items:center;gap:5px; }
  .btn:hover { background:var(--surface-2); }
  .btn:disabled { opacity:.45;cursor:not-allowed; }
  .btn.primary { background:var(--ink);color:var(--bg);border-color:var(--ink); }
  .btn.primary:hover:not(:disabled) { background:var(--ink-2); }
  .btn.danger { background:var(--critical);color:#fff;border-color:var(--critical); }
  .btn.warn-btn { color:var(--warn);border-color:var(--warn);background:var(--warn-soft); }
  .btn.accent-btn { background:var(--accent);color:#fff;border-color:var(--accent); }
  .btn.sm { padding:4px 10px;font-size:11.5px; }
  .btn.ghost { border-color:transparent;background:transparent; }
  .btn.ghost:hover { background:var(--surface-2); }

  /* Pills */
  .pill { display:inline-flex;align-items:center;gap:4px;padding:2px 6px;border-radius:999px;font-size:10.5px;border:1px solid var(--line-2);color:var(--ink-2);background:var(--surface); }
  .pill.crit { background:var(--critical-soft);color:var(--critical);border-color:var(--critical); }
  .pill.warn { background:var(--warn-soft);color:var(--warn);border-color:var(--warn); }
  .pill.ok { background:var(--ok-soft);color:var(--ok);border-color:var(--ok); }
  .pill.info { background:var(--info-soft);color:var(--info);border-color:var(--info); }
  .pill .d { width:5px;height:5px;border-radius:50%;background:currentColor; }

  /* ── SAFETY-2: Three-tier pharmacy alerts ── */
  .rx-row { padding:10px 14px;border-bottom:1px solid var(--line); }
  .rx-main { display:grid;grid-template-columns:1fr 130px;gap:10px;align-items:center; }
  /* Advisory: inline pill — same as before */
  /* Warning: callout box */
  .alert-warn-callout { display:flex;align-items:flex-start;gap:9px;margin-top:8px;padding:8px 10px;border-left:3px solid var(--warn);background:var(--warn-soft);border-radius:0 4px 4px 0; }
  .alert-warn-callout .txt { font-size:12px;color:var(--warn);font-weight:500; }
  /* Critical hold: full-width banner + acknowledge */
  .alert-crit-hold { margin-top:8px;border:1.5px solid var(--critical);border-radius:var(--r);background:var(--critical-soft);overflow:hidden; }
  .alert-crit-hold .hd { display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--critical);color:#fff; }
  .alert-crit-hold .hd span { font-size:12px;font-weight:600;flex:1; }
  .alert-crit-hold .body { padding:8px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px; }
  .alert-crit-hold .body p { margin:0;font-size:12px;color:var(--critical);font-weight:500; }
  .ack-btn { display:flex;align-items:center;gap:6px;padding:5px 10px;border:1.5px solid var(--critical);border-radius:4px;background:#fff;color:var(--critical);font-size:11.5px;font-family:inherit;cursor:pointer;font-weight:600;white-space:nowrap; }
  .ack-btn.acked { background:var(--ok-soft);color:var(--ok);border-color:var(--ok); }
  .unack-warning { display:flex;align-items:center;gap:8px;padding:10px 14px;background:var(--critical-soft);border-top:1px solid var(--critical);font-size:12px;color:var(--critical);font-family:'IBM Plex Mono',monospace; }

  /* ── Agents ── */
  .agents-grid { padding:18px 26px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px; }
  .agent-card { border:1px solid var(--line);border-radius:var(--rl);background:var(--surface);padding:14px;display:flex;flex-direction:column;gap:9px;position:relative; }
  .agent-status { display:inline-flex;align-items:center;gap:5px;font-size:10.5px;color:var(--ok); }
  .caps { display:flex;flex-wrap:wrap;gap:3px; }
  .cap { font-family:'IBM Plex Mono',monospace;font-size:10px;padding:2px 5px;border:1px solid var(--line);border-radius:3px;color:var(--muted);background:var(--bg); }
  .agent-meta { display:flex;gap:10px;padding-top:8px;border-top:1px dashed var(--line);font-size:11px;color:var(--muted); }
  .agent-meta strong { color:var(--ink);font-weight:500;font-family:'IBM Plex Mono',monospace; }

  /* ── Radiology ── */
  .rad-grid { padding:18px 26px;display:grid;grid-template-columns:1fr 330px;gap:16px; }
  .rad-viewer { background:var(--surface);border:1px solid var(--line);border-radius:var(--rl);overflow:hidden; }
  .rad-canvas { aspect-ratio:1.1/1;background:#0a0a0a;background-image:radial-gradient(ellipse 60% 50% at 50% 50%,#2a2a2a,#050505 75%);position:relative; }
  .rad-canvas::before { content:"";position:absolute;inset:14%;border-radius:50%/60%;background:radial-gradient(ellipse at 50% 60%,#585858,#1a1a1a 70%,transparent 95%);filter:blur(0.4px); }
  .rad-ovl { position:absolute;border:1.5px solid #f59e0b;border-radius:4px;pointer-events:none; }
  .rad-ovl::after { content:attr(data-label);position:absolute;top:-20px;left:-1px;font-family:'IBM Plex Mono',monospace;font-size:10px;background:#f59e0b;color:#000;padding:1px 4px;border-radius:2px; }
  .rad-ovl.crit { border-color:var(--critical); }
  .rad-ovl.crit::after { background:var(--critical);color:white; }
  .rad-side { display:flex;flex-direction:column;gap:12px; }
  .panel { border:1px solid var(--line);border-radius:var(--rl);background:var(--surface);overflow:hidden; }
  .panel-h { padding:10px 12px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;background:var(--surface-2); }
  .panel-h h4 { margin:0;font-size:12.5px;font-weight:500; }
  .panel-b { padding:10px 12px; }
  .finding { display:flex;align-items:center;gap:9px;padding:7px 0;border-bottom:1px dashed var(--line); }
  .finding:last-child { border:0;padding-bottom:0; }
  .finding:first-child { padding-top:0; }
  .finding .dot { width:7px;height:7px;border-radius:50%;flex:0 0 7px; }
  .finding .ftxt { flex:1;font-size:12.5px; }
  .finding .pct { font-family:'IBM Plex Mono',monospace;font-size:11.5px;color:var(--muted); }
  .similar { display:grid;grid-template-columns:repeat(4,1fr);gap:6px; }
  .sim-case { aspect-ratio:1;border-radius:4px;background:linear-gradient(135deg,#1a1a1a,#2a2a2a);position:relative;border:1px solid var(--line);overflow:hidden; }
  .sim-case::before { content:"";position:absolute;inset:22%;border-radius:50%/60%;background:radial-gradient(ellipse at 50% 55%,#4a4a4a,#1a1a1a 70%,transparent); }
  .sim-case .lab { position:absolute;bottom:3px;left:3px;font-family:'IBM Plex Mono',monospace;font-size:9px;color:rgba(255,255,255,.7);background:rgba(0,0,0,.5);padding:1px 3px;border-radius:2px; }
  /* Radiology two-step confirm */
  .rad-confirm { margin-top:10px;border:1.5px solid var(--accent);border-radius:var(--r);background:var(--accent-soft);padding:10px 12px; }
  .rad-confirm p { margin:0 0 8px;font-size:12.5px;color:var(--accent-ink);font-weight:500; }

  /* ── Vitals ── */
  .vitals-grid { padding:18px 26px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px; }
  .vital-card { background:var(--surface);border:1px solid var(--line);border-radius:var(--rl);padding:16px;position:relative; }
  .vital-card .vlbl { font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted); }
  .vital-card .vval { font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:500;letter-spacing:-0.02em;margin-top:3px; }
  .vital-card .vval .vunit { font-size:13px;color:var(--muted);margin-left:5px; }
  .vital-card .vtrend { margin-top:12px;height:48px; }
  .vital-card.ok .vval { color:var(--ok); } .vital-card.warn .vval { color:var(--warn); } .vital-card.crit .vval { color:var(--critical); }
  .vital-fresh { position:absolute;top:12px;right:12px; }
  /* SAFETY-3: stale vitals border */
  .vital-card.stale { border-color:var(--warn);border-width:1.5px; }

  /* ── Documentation ── */
  .doc-grid { padding:18px 26px;display:grid;grid-template-columns:1fr 270px;gap:16px; }

  /* ── Canvas ── */
  .canvas-page { display:grid;grid-template-columns:270px 1fr;height:100%; }
  .gen-chat { border-right:1px solid var(--line);background:var(--surface);display:flex;flex-direction:column; }
  .gen-msgs { flex:1;overflow-y:auto;padding:12px 14px;display:flex;flex-direction:column;gap:10px; }
  .gmsg { font-size:12.5px; }
  .gmsg.bot { color:var(--ink-2); }
  .gmsg.user { background:var(--ink);color:var(--bg);padding:7px 11px;border-radius:10px 10px 2px 10px;align-self:flex-end;max-width:80%; }
  .gen-foot { border-top:1px solid var(--line);padding:10px 12px; }
  .suggs { display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px; }
  .sugg { font-size:11px;padding:3px 8px;border-radius:999px;border:1px solid var(--line-2);color:var(--ink-2);background:var(--bg);cursor:pointer; }
  .sugg:hover { background:var(--surface-2); }
  .gen-input { display:flex;align-items:center;gap:7px;border:1px solid var(--line-2);border-radius:var(--r);padding:3px 3px 3px 10px;background:var(--bg); }
  .gen-input input { flex:1;background:transparent;border:0;outline:0;font:inherit;color:inherit;padding:5px 0;font-size:12.5px; }
  .gen-input button { width:28px;height:28px;border:0;border-radius:4px;background:var(--accent);color:white;cursor:pointer;display:grid;place-items:center; }
  .canvas-stage { background:var(--bg);background-image:radial-gradient(circle,var(--line-2) 1px,transparent 1px);background-size:20px 20px;overflow:auto;position:relative; }
  .canvas-empty { height:100%;display:grid;place-items:center;color:var(--muted);text-align:center; }
  .canvas-cards { padding:24px;display:flex;flex-wrap:wrap;gap:16px; }
  .cv-card { background:var(--surface);border:1px solid var(--line);border-radius:var(--rl);min-width:270px;max-width:330px; }
  .cv-card .ch { padding:7px 10px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;font-size:11px;color:var(--muted); }
  .cv-card .cb { padding:12px; }

  /* Empty / pending states */
  .empty-state { padding:28px 20px;text-align:center;color:var(--muted); }
  .empty-state .ei { width:40px;height:40px;border-radius:50%;border:1px dashed var(--line-2);display:grid;place-items:center;margin:0 auto 10px;color:var(--muted-2); }
  .pending-lbl { display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--muted);font-family:'IBM Plex Mono',monospace;padding:2px 7px;border-radius:3px;border:1px solid var(--line); }

  /* Spark */
  .spark { width:100%;height:100%; }
`;

/* ─── Data ─── */
const PATIENTS = [
  { id:"P-2418", name:"Margaret R.", age:67, sex:"F", esi:1, chief:"Substernal chest pain, dyspnea x 40 min", arrived:"11:42", waited:0, vitals:{hr:118,bp:"98/62",spo2:92,rr:24,temp:37.1}, redFlags:["ST elevation V2-V4","Troponin pending"], status:"resus", dataAge:2 },
  { id:"P-2419", name:"Daniel K.", age:45, sex:"M", esi:2, chief:"Sudden left hemiparesis, slurred speech (FAST+)", arrived:"11:38", waited:4, vitals:{hr:92,bp:"168/104",spo2:97,rr:18,temp:36.8}, redFlags:["LKW < 2h","tPA window"], status:"stroke", dataAge:6 },
  { id:"P-2420", name:"Aisha N.", age:32, sex:"F", esi:3, chief:"RLQ abdominal pain, fever 39.2°C, n/v", arrived:"11:21", waited:21, vitals:{hr:102,bp:"124/78",spo2:99,rr:18,temp:39.2}, redFlags:[], status:"wait", dataAge:21 },
  { id:"P-2421", name:"Tomás G.", age:28, sex:"M", esi:4, chief:"Right ankle inversion injury, moderate swelling", arrived:"11:08", waited:34, vitals:{hr:78,bp:"122/76",spo2:99,rr:14,temp:36.6}, redFlags:[], status:"wait", dataAge:3 },
  { id:"P-2422", name:"Eleanor W.", age:55, sex:"F", esi:5, chief:"Prescription refill — losartan, metformin", arrived:"10:55", waited:47, vitals:{hr:72,bp:"132/82",spo2:98,rr:12,temp:36.5}, redFlags:[], status:"wait", dataAge:47 },
  { id:"P-2423", name:"Hiroshi T.", age:71, sex:"M", esi:2, chief:"Syncope episode, second this week", arrived:"11:30", waited:12, vitals:{hr:54,bp:"108/68",spo2:96,rr:16,temp:36.7}, redFlags:["Bradycardia"], status:"wait", dataAge:4 },
];

const AGENTS = [
  { name:"Triage", color:"var(--critical)", desc:"ESI scoring, red-flag detection, queue routing", caps:["esi_score","red_flag","fast_track"], model:"ClinicalBERT-Lg", calls:"1.2k/d", latency:"240ms" },
  { name:"Diagnostic", color:"var(--accent)", desc:"Differential generation from chief complaint + vitals", caps:["differential","icd10","test_recommend"], model:"MedGemma-27B", calls:"642/d", latency:"1.4s" },
  { name:"Radiology", color:"#0369a1", desc:"X-ray, CT, MRI lesion localization & description", caps:["xray","ct","mri","knn_search"], model:"MedImageInsight", calls:"318/d", latency:"2.1s" },
  { name:"Pharmacy", color:"var(--warn)", desc:"Drug interactions, dosing, contraindication checks", caps:["interactions","dosage","renal_adj"], model:"RxNorm + GPT-Med", calls:"890/d", latency:"180ms" },
  { name:"Vitals Monitor", color:"var(--ok)", desc:"Continuous MEWS scoring & deterioration alerts", caps:["mews","anomaly","trend"], model:"TimeGAN-Med", calls:"stream", latency:"30ms" },
  { name:"Documentation", color:"#7c3aed", desc:"SOAP notes, discharge summaries from voice + chart", caps:["soap","discharge","billing"], model:"Whisper + Claude", calls:"455/d", latency:"3.2s" },
  { name:"Research", color:"#0891b2", desc:"Literature search, guideline lookup, trial matching", caps:["pubmed","uptodate","trials"], model:"BioBERT-Sage", calls:"210/d", latency:"1.8s" },
  { name:"Coordinator", color:"var(--ink)", desc:"Routes between agents, consensus, safety checks", caps:["routing","consensus","safety"], model:"Claude Opus", calls:"5.4k/d", latency:"120ms" },
  { name:"GenUI", color:"#9333ea", desc:"On-demand dashboards & forms generated for context", caps:["component_gen","layout","forms"], model:"Claude Sonnet", calls:"82/d", latency:"4.1s" },
];

const DDX = [
  { name:"Acute coronary syndrome", code:"I20.0", confidence:0.84 },
  { name:"Aortic dissection", code:"I71.0", confidence:0.41 },
  { name:"Pulmonary embolism", code:"I26.9", confidence:0.37 },
  { name:"Pericarditis", code:"I30.9", confidence:0.18 },
  { name:"GERD / esophageal spasm", code:"K21.9", confidence:0.11 },
];

/* ─── Icons ─── */
const I = {
  triage:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M3 12h3l3-7 4 14 3-7h5"/></svg>,
  agents:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="8" r="3"/><path d="M5 21c1-4 4-6 7-6s6 2 7 6"/></svg>,
  rad:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="12" cy="12" r="5"/><path d="M3 12h2M19 12h2M12 3v2M12 19v2"/></svg>,
  vitals:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M3 12h4l2-5 4 10 2-5h6"/></svg>,
  doc:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M8 3h7l5 5v13a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v6h6M9 13h7M9 17h5"/></svg>,
  rx:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 4h6a4 4 0 0 1 0 8H6V4z"/><path d="M6 12l8 8M11 14l4 4"/></svg>,
  research:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>,
  canvas:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 3v18"/></svg>,
  search:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>,
  bell:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M6 16V11a6 6 0 1 1 12 0v5l1 2H5l1-2z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>,
  sun:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/></svg>,
  moon:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>,
  send:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 12h14M13 5l7 7-7 7"/></svg>,
  alert:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 3 2 21h20L12 3z"/><path d="M12 10v5M12 18v.01"/></svg>,
  check:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="m5 12 5 5L20 7"/></svg>,
  flag:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M5 21V4M5 4h12l-2 4 2 4H5"/></svg>,
  plus:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 5v14M5 12h14"/></svg>,
  clock:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>,
  x:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M18 6 6 18M6 6l12 12"/></svg>,
  shield:(p)=><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
};

/* ─── Helpers ─── */
function Spark({ data, color="var(--accent)" }) {
  const w=260,h=48;
  const mn=Math.min(...data),mx=Math.max(...data),rng=mx-mn||1;
  const pts=data.map((v,i)=>[i/(data.length-1)*w, h-((v-mn)/rng)*(h-6)-3]);
  const line=pts.map(([x,y],i)=>`${i?"L":"M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="spark" preserveAspectRatio="none">
      <path d={`${line} L${w} ${h} L0 ${h} Z`} fill={color} opacity="0.12" stroke="none"/>
      <path d={line} fill="none" stroke={color} strokeWidth="1.5"/>
    </svg>
  );
}

/* SAFETY-3: freshness badge */
function FreshBadge({ ageMin }) {
  const cls = ageMin <= 5 ? "" : ageMin <= 15 ? " stale" : " old";
  const label = ageMin <= 5 ? `${ageMin}m ago ✓` : ageMin <= 15 ? `${ageMin}m ago ⚠` : `${ageMin}m ago — STALE`;
  return <span className={`fresh${cls}`}><I.clock style={{width:10,height:10}}/> {label}</span>;
}

/* ─── Sidebar ─── */
function Sidebar({ route, setRoute }) {
  const clinical = [
    { id:"triage", label:"Triage", Ico:I.triage, badge:"6" },
    { id:"agents", label:"Agents", Ico:I.agents, badge:"9/9" },
    { id:"radiology", label:"Radiology", Ico:I.rad, badge:"3" },
    { id:"vitals", label:"Vitals", Ico:I.vitals },
    { id:"documentation", label:"Documentation", Ico:I.doc },
    { id:"pharmacy", label:"Pharmacy", Ico:I.rx },
    { id:"research", label:"Research", Ico:I.research },
  ];
  return (
    <aside className="ma-sb">
      <div className="ma-brand">
        <div className="ma-mark">M+</div>
        <div className="ma-brand-name">MedAssist<small>St. Vincent · ED</small></div>
      </div>
      <div className="ma-nav-group">
        <div className="ma-nav-lbl">Clinical</div>
        {clinical.map(it=>(
          <div key={it.id} className={"ma-ni"+(route===it.id?" active":"")} onClick={()=>setRoute(it.id)}>
            <it.Ico className="ico" style={{width:13,height:13}}/>
            <span>{it.label}</span>
            {it.badge&&<span className="bdg">{it.badge}</span>}
          </div>
        ))}
        {/* UX-5: Canvas separated from clinical routes */}
        <div className="ma-nav-sep"/>
        <div className="ma-nav-lbl">Tools</div>
        <div className={"ma-ni"+(route==="canvas"?" active":"")} onClick={()=>setRoute("canvas")}>
          <I.canvas className="ico" style={{width:13,height:13}}/>
          <span>Canvas</span>
          <span className="bdg">GenUI</span>
        </div>
      </div>
      <div className="ma-ctx">
        <div className="ma-ctx-row"><span>Shift</span><strong>Dr. K. Patel</strong></div>
        <div className="ma-ctx-row"><span>On since</span><strong className="mono">07:00</strong></div>
        <div className="ma-ctx-row"><span>Census</span><strong className="mono">23 / 28</strong></div>
        <div className="ma-ctx-row" style={{marginTop:4,borderTop:"1px dashed var(--line)",paddingTop:6}}>
          <span className="pulse"><span className="pdot"/>9 agents online</span>
          <span className="mono" style={{color:"var(--muted)",fontSize:10}}>v2.1.0</span>
        </div>
      </div>
    </aside>
  );
}

/* ─── Topbar ─── */
function Topbar({ route, dark, setDark }) {
  const L = { triage:["Clinical","Triage queue"], agents:["System","Agent control"], radiology:["Clinical","Radiology read"], vitals:["Clinical","Vitals monitor"], documentation:["Clinical","Documentation"], pharmacy:["Clinical","Pharmacy review"], research:["Clinical","Research & evidence"], canvas:["Tools","GenUI canvas"] }[route]||["",""];
  return (
    <div className="ma-topbar">
      <div className="ma-crumbs">{L[0]} <span style={{color:"var(--muted-2)"}}>/</span> <strong>{L[1]}</strong></div>
      <div className="ma-top-right">
        <div className="ma-search"><I.search style={{width:12,height:12}}/><span>Search patients, MRN, drugs…</span><kbd>⌘K</kbd></div>
        <button className="icobtn"><I.bell style={{width:13,height:13}}/></button>
        <button className="icobtn" onClick={()=>setDark(d=>!d)}>{dark?<I.sun style={{width:13,height:13}}/>:<I.moon style={{width:13,height:13}}/>}</button>
      </div>
    </div>
  );
}

/* ─── Triage ─── */
function TriagePage() {
  const [sel,setSel]=useState(PATIENTS[0].id);
  const [filter,setFilter]=useState("all");
  const filtered=useMemo(()=>filter==="all"?PATIENTS:filter==="critical"?PATIENTS.filter(p=>p.esi<=2):PATIENTS.filter(p=>p.status==="wait"),[filter]);
  const counts={all:PATIENTS.length,critical:PATIENTS.filter(p=>p.esi<=2).length,waiting:PATIENTS.filter(p=>p.status==="wait").length};
  const esiC=[1,2,3,4,5].map(n=>PATIENTS.filter(p=>p.esi===n).length);
  const patient=PATIENTS.find(p=>p.id===sel);
  return (
    <>
      <div className="banner"><I.alert style={{width:13,height:13}}/><span><strong>AI-ASSISTED TRIAGE</strong> — All ESI scores require clinician verification. ESI 1–2 auto-page attending. HIPAA audit log active.</span></div>
      <div className="ph">
        <div><h1>Triage queue</h1><div className="ph-sub">Live ED queue — sorted by acuity. Continuous MEWS monitoring on all admitted patients.</div></div>
        <div className="stat-row">
          <div className="stat"><div className="k">ESI 1</div><div className="v crit">{esiC[0]}</div></div>
          <div className="stat"><div className="k">ESI 2</div><div className="v" style={{color:"#ea580c"}}>{esiC[1]}</div></div>
          <div className="stat"><div className="k">ESI 3</div><div className="v warn">{esiC[2]}</div></div>
          <div className="stat"><div className="k">ESI 4</div><div className="v ok">{esiC[3]}</div></div>
          <div className="stat"><div className="k">ESI 5</div><div className="v">{esiC[4]}</div></div>
          <div className="stat"><div className="k">Median wait</div><div className="v">14<span style={{fontSize:10,color:"var(--muted)"}}> min</span></div></div>
        </div>
      </div>
      <div className="queue">
        <div className="qlist">
          <div className="qtoolbar">
            {[{id:"all",lab:"All"},{id:"critical",lab:"ESI 1–2"},{id:"waiting",lab:"Waiting"}].map(f=>(
              <button key={f.id} className="qfil" aria-pressed={filter===f.id} onClick={()=>setFilter(f.id)}>{f.lab} <span style={{fontFamily:"monospace",opacity:.7,fontSize:11}}>{counts[f.id]}</span></button>
            ))}
            <div style={{marginLeft:"auto",fontSize:11,color:"var(--muted)",fontFamily:"monospace"}}>11:43:12</div>
          </div>
          {filtered.map(p=>(
            <div key={p.id} className={"prow"+(sel===p.id?" sel":"")} onClick={()=>setSel(p.id)}>
              <div className={"esib e"+p.esi}/>
              <div className="pid">{p.name.split(" ").map(s=>s[0]).join("")}</div>
              <div>
                <div className="pname">{p.name} <span style={{color:"var(--muted)",fontWeight:400,fontSize:11.5}}>· {p.age}{p.sex} · {p.id}</span></div>
                <div className="pchief">{p.chief}</div>
                {p.redFlags.length>0&&<div style={{marginTop:5,display:"flex",gap:3,flexWrap:"wrap"}}>{p.redFlags.map(rf=><span key={rf} className="pill crit"><span className="d"/>{rf}</span>)}</div>}
              </div>
              <div style={{display:"flex",flexDirection:"column",gap:3,alignItems:"flex-end"}}>
                <span className={"epill ep"+p.esi}>ESI-{p.esi}</span>
                <span style={{fontSize:10.5,color:"var(--muted)"}}>{p.status==="resus"?"Resus 2":p.status==="stroke"?"Stroke bay":"Waiting"}</span>
              </div>
              <div className={"pwait"+(p.waited>30?" over":"")}>
                <div style={{fontSize:13,color:"var(--ink)"}}>{p.waited}<span style={{fontSize:10,color:"var(--muted)"}}>m</span></div>
                <div style={{fontSize:10}}>arr {p.arrived}</div>
              </div>
            </div>
          ))}
        </div>
        {patient&&<PatientDetail patient={patient}/>}
      </div>
    </>
  );
}

/* SAFETY-1 + UX-2 + UX-3 */
function PatientDetail({ patient }) {
  /* Orders: all unchecked by default — clinician selects actively */
  const ORDERS = [
    { id:"ecg", lab:"12-lead ECG", stat:true, why:"rule out STEMI" },
    { id:"trop", lab:"Troponin I (high-sens)", stat:true, why:"ACS evaluation" },
    { id:"cbc", lab:"CBC, BMP, lipid panel", stat:false, why:"baseline" },
    { id:"cxr", lab:"Portable CXR", stat:false, why:"r/o pneumothorax" },
    { id:"asa", lab:"ASA 325 mg PO chewed", stat:true, why:"ACS pathway" },
  ];
  const [checked,setChecked]=useState({});
  const [step,setStep]=useState("idle"); // idle | confirm | signed
  const toggle=id=>setChecked(c=>({...c,[id]:!c[id]}));
  const selectedOrders=ORDERS.filter(o=>checked[o.id]);

  return (
    <div className="det">
      <div className="det-head">
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:10}}>
          <div>
            <div className="det-name">{patient.name}, {patient.age}</div>
            <div style={{color:"var(--muted)",fontSize:12,marginTop:2}} className="mono">MRN {patient.id} · {patient.sex} · arrived {patient.arrived}</div>
          </div>
          <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:5}}>
            <span className={"epill ep"+patient.esi} style={{fontSize:12,padding:"3px 8px"}}>ESI-{patient.esi}</span>
            {/* SAFETY-3: per-patient data freshness */}
            <FreshBadge ageMin={patient.dataAge}/>
          </div>
        </div>
        <div className="det-grid">
          {/* UX-1: Show both SBP and DBP, no redundant "(SBP)" label */}
          <div className="kv"><div className="k">HR</div><div className={"v"+(patient.vitals.hr>110?" warn":"")}>{patient.vitals.hr} bpm</div></div>
          <div className="kv"><div className="k">BP</div><div className={"v"+(parseInt(patient.vitals.bp)<100?" crit":"")}>{patient.vitals.bp} mmHg</div></div>
          <div className="kv"><div className="k">SpO₂</div><div className={"v"+(patient.vitals.spo2<94?" warn":"")}>{patient.vitals.spo2}%</div></div>
          <div className="kv"><div className="k">Temp · RR</div><div className={"v"+(patient.vitals.temp>38.5?" warn":"")}>{patient.vitals.temp}°C · {patient.vitals.rr}/min</div></div>
        </div>
      </div>

      <div className="det-sec"><h3>Chief complaint</h3><div style={{fontSize:13.5}}>{patient.chief}</div></div>

      <div className="det-sec">
        {/* UX-2: AI badge bigger + tooltip explaining confidence */}
        <h3>
          Differential diagnosis
          <span className="ai-bdg">
            AI · MedGemma 27B
            <span className="ai-tip">Confidence = model posterior probability from 12,408 similar presentations. Not a diagnostic guarantee — requires clinician verification before acting.</span>
          </span>
        </h3>
        <div className="ddx">
          {DDX.map(d=>(
            <div key={d.code} className="ddx-row">
              {/* UX-3: tooltip on confidence bar */}
              <div style={{fontSize:13}}>{d.name} <code style={{fontFamily:"monospace",fontSize:10.5,color:"var(--muted)"}}>{d.code}</code></div>
              <div title={`${(d.confidence*100).toFixed(0)}% — model posterior probability. Values >70% indicate primary hypothesis; 30–70% rule-out candidates; <30% low-probability.`} style={{cursor:"help"}}>
                <div className="bar"><span style={{width:`${d.confidence*100}%`,background:d.confidence>.7?"var(--critical)":d.confidence>.3?"var(--warn)":"var(--accent)"}}/></div>
              </div>
              <div style={{fontFamily:"monospace",fontSize:12,textAlign:"right"}}>{(d.confidence*100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
        <div style={{fontSize:11,color:"var(--muted)",marginTop:8,fontFamily:"monospace"}}>Generated 11:42:08 · 6 features · 1.4s · n=12,408 cases · hover bars for methodology</div>
      </div>

      {/* SAFETY-1: Orders unchecked by default */}
      <div className="det-sec">
        <h3>
          Recommended orders
          <span className="ai-bdg">AI · {ORDERS.length} suggestions</span>
          <span style={{fontSize:10.5,color:"var(--muted)",fontWeight:400,textTransform:"none",letterSpacing:0}}>— select to include in sign</span>
        </h3>
        <div className="orders-list">
          {ORDERS.map(o=>(
            <label key={o.id} className="order-item" onClick={()=>toggle(o.id)}>
              <input type="checkbox" checked={!!checked[o.id]} onChange={()=>toggle(o.id)} style={{accentColor:"var(--accent)"}}/>
              <span style={{fontSize:13,fontWeight:o.stat?500:400}}>{o.lab}</span>
              <span style={{fontSize:11,color:"var(--muted)",marginLeft:"auto"}}>{o.why}</span>
              {o.stat&&<span className="pill" style={{fontSize:9.5,background:"var(--warn-soft)",color:"var(--warn)",borderColor:"var(--warn)"}}>STAT</span>}
            </label>
          ))}
        </div>
        {selectedOrders.length===0&&<div style={{marginTop:8,fontSize:11.5,color:"var(--muted)"}}>No orders selected. Check items above to include in sign.</div>}
      </div>

      {/* SAFETY-1: Two-step confirm flow */}
      {step==="idle"&&(
        <div className="act-bar">
          <button className="btn primary" disabled={selectedOrders.length===0} onClick={()=>setStep("confirm")}>
            <I.shield style={{width:13,height:13}}/> Review & sign orders{selectedOrders.length>0?` (${selectedOrders.length})`:""}
          </button>
          <button className="btn"><I.flag style={{width:13,height:13}}/> Flag for review</button>
          <button className="btn" style={{marginLeft:"auto"}}>Open chart →</button>
        </div>
      )}
      {step==="confirm"&&(
        <div className="sign-confirm-box">
          <div className="sign-confirm-hd">
            <h4>Confirm — signing {selectedOrders.length} order{selectedOrders.length>1?"s":""}</h4>
            <button className="btn ghost sm" onClick={()=>setStep("idle")}><I.x style={{width:12,height:12}}/>Cancel</button>
          </div>
          <div className="sign-confirm-body">
            {selectedOrders.map(o=>(
              <div key={o.id} className="sign-order-line">
                <I.check style={{width:12,height:12,color:"var(--accent-ink)"}}/>
                <span>{o.lab}</span>
                {o.stat&&<span className="pill" style={{fontSize:9.5,background:"var(--warn-soft)",color:"var(--warn)",borderColor:"var(--warn)"}}>STAT</span>}
                <span style={{marginLeft:"auto",fontSize:11,color:"var(--muted)"}}>{o.why}</span>
              </div>
            ))}
          </div>
          <div className="sign-confirm-footer">
            <button className="btn accent-btn" onClick={()=>setStep("signed")}>
              <I.check style={{width:13,height:13}}/> Confirm & submit to EHR
            </button>
            <span style={{fontSize:11,color:"var(--accent-ink)"}}>Signed as Dr. K. Patel · {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      )}
      {step==="signed"&&(
        <div className="sign-done">
          <I.check style={{width:14,height:14}}/> {selectedOrders.length} order{selectedOrders.length>1?"s":""} submitted to EHR — Dr. K. Patel · {new Date().toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

/* ─── Agents ─── */
function AgentsPage() {
  return (
    <>
      <div className="ph">
        <div><h1>Agent control</h1><div className="ph-sub">Nine specialized clinical agents orchestrated by the Coordinator. All actions logged to HIPAA audit trail and require clinician sign-off.</div></div>
        <div className="stat-row">
          <div className="stat"><div className="k">Online</div><div className="v ok">9/9</div></div>
          <div className="stat"><div className="k">Calls/hr</div><div className="v">427</div></div>
          <div className="stat"><div className="k">P50 latency</div><div className="v">1.2s</div></div>
          <div className="stat"><div className="k">Pending</div><div className="v warn">3</div></div>
        </div>
      </div>
      <div className="agents-grid">
        {AGENTS.map(a=>(
          <div key={a.name} className="agent-card">
            <div style={{position:"absolute",top:0,left:0,width:3,height:"100%",background:a.color,borderRadius:"10px 0 0 10px"}}/>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:10}}>
              <div>
                <div style={{fontWeight:500,fontSize:13.5,letterSpacing:"-0.005em"}}>{a.name} agent</div>
                <div style={{color:"var(--muted)",fontSize:12,lineHeight:1.5,marginTop:3}}>{a.desc}</div>
              </div>
              <span className="agent-status"><span className="pdot"/>Online</span>
            </div>
            <div className="caps">{a.caps.map(c=><span key={c} className="cap">{c}</span>)}</div>
            <div className="agent-meta">
              <span>Model · <strong>{a.model}</strong></span>
              <span>Calls · <strong>{a.calls}</strong></span>
              <span>Lat · <strong>{a.latency}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ─── Radiology — UX-4: two-step approval ─── */
function RadiologyPage() {
  const [step,setStep]=useState("idle"); // idle | confirm | signed | flagged
  return (
    <>
      <div className="banner info"><I.alert style={{width:13,height:13}}/><span><strong>AI-ASSISTED READ</strong> — Findings are advisory only. Board-certified radiologist must sign final report. AI accuracy 91.3% (n=4,208 PA chest XR vs attending reads).</span></div>
      <div className="ph">
        <div><h1>Chest X-Ray · PA</h1><div className="ph-sub">Daniel K., 45M · Acquired 11:38 · MedImageInsight + MedGemma 4B</div></div>
        <div style={{display:"flex",gap:7,alignItems:"center"}}>
          <span className="pill info"><span className="d"/>Study #CR-3320</span>
          <span className="pill"><span className="d"/>1.4 MB · DICOM</span>
          <FreshBadge ageMin={6}/>
        </div>
      </div>
      <div className="rad-grid">
        <div className="rad-viewer">
          <div style={{display:"flex",gap:5,padding:"8px 12px",borderBottom:"1px solid var(--line)",background:"var(--surface-2)",alignItems:"center"}}>
            {["Pan","Zoom","W/L","Measure","Reset"].map(t=><button key={t} className="btn sm">{t}</button>)}
            <div style={{marginLeft:"auto",fontFamily:"monospace",fontSize:11,color:"var(--muted)"}}>512×512 · WL 50/350</div>
          </div>
          <div className="rad-canvas">
            <div className="rad-ovl" data-label="Infiltrate · 94%" style={{left:"32%",top:"55%",width:"16%",height:"14%"}}/>
            <div className="rad-ovl crit" data-label="Cardiomegaly · 87%" style={{left:"42%",top:"44%",width:"26%",height:"22%"}}/>
            <div style={{position:"absolute",top:8,left:8,fontFamily:"monospace",fontSize:10,color:"rgba(255,255,255,.6)"}}>R · PA · STANDING</div>
            <div style={{position:"absolute",bottom:8,right:8,fontFamily:"monospace",fontSize:10,color:"rgba(255,255,255,.6)"}}>MRN P-2419 · 11:38</div>
          </div>
          <div style={{padding:"8px 12px",fontFamily:"monospace",fontSize:11,color:"var(--muted)",display:"flex",justifyContent:"space-between",borderTop:"1px solid var(--line)"}}>
            <span>kVp 120 · mAs 4 · 0.3s</span><span>Slice 1/1 · Inspiration adequate</span>
          </div>
        </div>
        <div className="rad-side">
          <div className="panel">
            <div className="panel-h"><h4>AI findings</h4><span className="pill info"><span className="d"/>4 detected</span></div>
            <div className="panel-b">
              {[{c:"var(--critical)",t:"Bilateral infiltrates, lower lobes",p:94},{c:"var(--warn)",t:"Mild cardiomegaly",p:87},{c:"var(--ok)",t:"No pneumothorax identified",p:96},{c:"var(--warn)",t:"Costophrenic angles blunted bilaterally",p:82}].map(f=>(
                <div className="finding" key={f.t}><span className="dot" style={{background:f.c}}/><span className="ftxt">{f.t}</span><span className="pct">{f.p}%</span></div>
              ))}
            </div>
          </div>
          <div className="panel">
            <div className="panel-h"><h4>Similar cases</h4><span className="pill"><span className="d"/>KNN · n=4</span></div>
            <div className="panel-b">
              <div className="similar">{[{d:"0.12",lab:"PNA bil."},{d:"0.18",lab:"CHF"},{d:"0.21",lab:"ARDS"},{d:"0.24",lab:"Atypical PNA"}].map(c=><div className="sim-case" key={c.lab}><span className="lab">{c.d} · {c.lab}</span></div>)}</div>
              <div style={{marginTop:8,fontSize:11.5,color:"var(--muted)"}}>Closest: <strong style={{color:"var(--ink)"}}>Bilateral pneumonia</strong> (cosine 0.12)</div>
            </div>
          </div>
          <div className="panel">
            <div className="panel-h"><h4>AI impression</h4></div>
            <div className="panel-b">
              <p className="serif" style={{margin:0,fontSize:13,lineHeight:1.55}}>Bilateral lower-lobe infiltrates with mild cardiomegaly. Differential includes CAP vs cardiogenic edema. Recommend BNP, troponin correlation; CT if worsening.</p>

              {/* UX-4: Two-step radiology approval */}
              {step==="idle"&&(
                <div style={{display:"flex",gap:6,marginTop:12}}>
                  <button className="btn sm primary" onClick={()=>setStep("confirm")}><I.check style={{width:12,height:12}}/> Approve & sign</button>
                  <button className="btn sm warn-btn" onClick={()=>setStep("flagged")}><I.flag style={{width:12,height:12}}/> Flag — needs read</button>
                </div>
              )}
              {step==="confirm"&&(
                <div className="rad-confirm">
                  <p>Sign as final AI-assisted read? This will notify the attending radiologist for co-signature.</p>
                  <div style={{display:"flex",gap:6}}>
                    <button className="btn sm accent-btn" onClick={()=>setStep("signed")}><I.check style={{width:12,height:12}}/> Yes, approve & sign</button>
                    <button className="btn sm ghost" onClick={()=>setStep("idle")}><I.x style={{width:12,height:12}}/> Cancel</button>
                  </div>
                </div>
              )}
              {step==="signed"&&<div style={{marginTop:10,fontSize:11,color:"var(--ok)",fontFamily:"monospace"}}>✓ Signed — Dr. K. Patel · {new Date().toLocaleTimeString()} · Attending co-sign pending</div>}
              {step==="flagged"&&<div style={{marginTop:10,fontSize:11,color:"var(--warn)",fontFamily:"monospace"}}>⚐ Flagged for senior radiologist review</div>}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ─── Vitals — SAFETY-3: freshness per card ─── */
function VitalsPage() {
  const hr=[82,84,86,90,94,98,102,108,112,118,116,118];
  const bp=[128,126,122,118,114,108,104,100,98,98,96,98];
  const spo2=[98,98,97,97,96,95,94,93,92,92,93,92];
  const rr=[16,16,18,18,20,20,22,22,24,24,24,24];
  const cards=[
    {label:"Heart rate",val:"118",unit:"bpm",tag:"Tachycardia",cls:"warn",data:hr,color:"var(--warn)",dbp:null,age:2},
    {label:"Blood pressure",val:"98 / 62",unit:"mmHg",tag:"Hypotension",cls:"crit",data:bp,color:"var(--critical)",age:2},
    {label:"SpO₂",val:"92",unit:"%",tag:"Hypoxia",cls:"warn",data:spo2,color:"var(--warn)",age:2},
    {label:"Respiratory rate",val:"24",unit:"/min",tag:"Tachypnea",cls:"warn",data:rr,color:"var(--warn)",age:18},
  ];
  return (
    <>
      <div className="ph">
        <div><h1>Vitals · live monitor</h1><div className="ph-sub">Margaret R. (P-2418) · Resus 2 · Streaming since 11:42 · MEWS 7 (high)</div></div>
        <div className="stat-row">
          <div className="stat"><div className="k">MEWS</div><div className="v crit">7</div></div>
          <div className="stat"><div className="k">Trend (10m)</div><div className="v warn">↑</div></div>
          <div className="stat"><div className="k">Last alert</div><div className="v">2m ago</div></div>
        </div>
      </div>
      <div className="vitals-grid">
        {cards.map(v=>(
          <div key={v.label} className={"vital-card "+v.cls+(v.age>15?" stale":"")}>
            <div className="vital-fresh"><FreshBadge ageMin={v.age}/></div>
            <div className="vlbl">{v.label}</div>
            {/* UX-1: BP shows both SBP and DBP naturally */}
            <div className="vval">{v.val}<span className="vunit">{v.unit}</span></div>
            <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:"var(--muted)",marginTop:5}}>
              <span>MEWS contributing</span>
              <span className={"pill "+v.cls}><span className="d"/>{v.tag}</span>
            </div>
            {v.age>15&&<div style={{fontSize:11,color:"var(--warn)",marginTop:4,fontFamily:"monospace"}}>⚠ Data may be stale — verify sensor connection</div>}
            <div className="vtrend"><Spark data={v.data} color={v.color}/></div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ─── Documentation ─── */
function DocumentationPage() {
  const [text,setText]=useState("SUBJECTIVE\n67F with substernal chest pain radiating to L arm × 40 min, dyspnea, diaphoresis. PMH: HTN, HLD.\n\nOBJECTIVE\nVitals: HR 118, BP 98/62 mmHg, SpO₂ 92% RA, RR 24/min, T 37.1°C.\nExam: ill-appearing, diaphoretic. Bibasilar crackles. Tachycardic, no murmur.\n\nASSESSMENT\n1. Acute coronary syndrome — STEMI V2–V4 elevation.\n2. Acute decompensated heart failure.\n\nPLAN\n- Cath lab activated. ASA 325 mg given, heparin gtt started.\n- O₂ NC 4 L/min, SpO₂ goal ≥94%.\n- Lisinopril HELD — SBP 98 mmHg.");
  return (
    <>
      <div className="ph">
        <div><h1>Documentation</h1><div className="ph-sub">SOAP note · drafted from voice + chart · awaiting clinician sign</div></div>
        <div className="stat-row">
          <div className="stat"><div className="k">Auto-coded</div><div className="v">7</div></div>
          <div className="stat"><div className="k">Saved</div><div className="v ok">just now</div></div>
          <div className="stat"><div className="k">Confidence</div><div className="v">92%</div></div>
        </div>
      </div>
      <div className="doc-grid">
        <div className="panel">
          <div className="panel-h"><h4>Patient encounter — Margaret R.</h4><span className="pill info"><span className="d"/>Draft</span></div>
          <textarea value={text} onChange={e=>setText(e.target.value)} style={{width:"100%",minHeight:320,border:0,outline:0,padding:16,fontFamily:"'IBM Plex Serif',serif",fontSize:13.5,lineHeight:1.7,background:"var(--surface)",color:"var(--ink)",resize:"vertical"}}/>
          <div style={{display:"flex",gap:7,padding:10,borderTop:"1px solid var(--line)"}}>
            <button className="btn primary"><I.check style={{width:13,height:13}}/> Sign & finalize</button>
            <button className="btn">Save draft</button>
            <span style={{marginLeft:"auto",fontSize:11,color:"var(--muted)",alignSelf:"center",fontFamily:"monospace"}}>{text.length} chars · auto-saved</span>
          </div>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:12}}>
          <div className="panel">
            <div className="panel-h"><h4>ICD-10 codes</h4></div>
            <div className="panel-b" style={{display:"flex",flexDirection:"column",gap:5}}>
              {[["I21.3","STEMI unspecified"],["I50.21","Acute systolic CHF"],["I10","Essential hypertension"],["E78.5","Hyperlipidemia"]].map(([c,d])=>(
                <div key={c} style={{display:"flex",alignItems:"center",gap:8,padding:"5px 7px",border:"1px solid var(--line)",borderRadius:4}}>
                  <span className="mono" style={{fontWeight:500,color:"var(--accent-ink)",fontSize:12}}>{c}</span>
                  <span style={{fontSize:12,color:"var(--ink-2)"}}>{d}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="panel">
            <div className="panel-h"><h4>Billing</h4></div>
            <div className="panel-b">
              <div style={{fontSize:11.5,color:"var(--muted)"}}>Estimated E/M level</div>
              <div className="mono" style={{fontSize:20,marginTop:2}}>99285 · L5</div>
              <div style={{marginTop:8,fontSize:11,color:"var(--muted)"}}>High complexity · high-risk MDM</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ─── Pharmacy — SAFETY-2: three-tier alert severity ─── */
function PharmacyPage() {
  const [acked,setAcked]=useState({});
  const meds=[
    { id:"asa", d:"Aspirin 81 mg PO QD", note:"ACS pathway", lastGiven:"11:38", tier:null },
    { id:"atorv", d:"Atorvastatin 80 mg PO QHS", note:"high-intensity statin", lastGiven:"21:00 (yesterday)", tier:null },
    { id:"hep", d:"Heparin 18 U/kg/hr IV", note:"weight-adjusted", lastGiven:"11:40", tier:"warning",
      alert:"Renal dose adjust recommended — CrCl 38 mL/min. Consider anti-Xa monitoring." },
    { id:"lisin", d:"Lisinopril 20 mg PO QD", note:"outpatient antihypertensive", lastGiven:"06:00",
      tier:"critical", alert:"HOLD — SBP 98 mmHg (< 100 mmHg threshold). Administering will worsen haemodynamic instability. Do not give until BP ≥ 100 mmHg." },
    { id:"metf", d:"Metformin 1000 mg PO BID", note:"outpatient antidiabetic", lastGiven:"06:00",
      tier:"warning", alert:"Hold pre-contrast: CT chest planned. Resume ≥48h after contrast if eGFR stable." },
  ];
  const criticalUnacked=meds.filter(m=>m.tier==="critical"&&!acked[m.id]);
  return (
    <>
      <div className="ph">
        <div><h1>Pharmacy review</h1><div className="ph-sub">Drug interactions, dosing, contraindications · checked against patient labs & allergies</div></div>
        {criticalUnacked.length>0&&(
          <div style={{display:"flex",alignItems:"center",gap:8,padding:"7px 12px",background:"var(--critical-soft)",border:"1px solid var(--critical)",borderRadius:"var(--r)",fontSize:12.5,color:"var(--critical)",fontWeight:500}}>
            <I.alert style={{width:13,height:13}}/>{criticalUnacked.length} critical hold{criticalUnacked.length>1?"s":""} require acknowledgement
          </div>
        )}
      </div>
      <div style={{padding:20}}>
        <div className="panel" style={{maxWidth:900}}>
          <div className="panel-h">
            <h4>Margaret R. — active medications</h4>
            <div style={{display:"flex",gap:6}}>
              {criticalUnacked.length>0&&<span className="pill crit"><span className="d"/>{criticalUnacked.length} critical hold</span>}
              <span className="pill warn"><span className="d"/>{meds.filter(m=>m.tier==="warning").length} warnings</span>
            </div>
          </div>
          {meds.map(m=>(
            <div key={m.id} className="rx-row">
              <div className="rx-main">
                <div>
                  <div style={{fontWeight:500,fontSize:13.5}}>{m.d}</div>
                  <div style={{fontSize:11.5,color:"var(--muted)",marginTop:2}}>{m.note}</div>
                </div>
                <div style={{display:"flex",flexDirection:"column",gap:4,alignItems:"flex-end"}}>
                  <span style={{fontSize:11,color:"var(--muted)",fontFamily:"monospace"}}>Last: {m.lastGiven}</span>
                  {m.tier===null&&<span className="pill ok"><span className="d"/>No alerts</span>}
                </div>
              </div>
              {/* Advisory: pill (if we had one — none in this data) */}
              {/* Warning: callout with left amber border */}
              {m.tier==="warning"&&(
                <div className="alert-warn-callout">
                  <I.alert style={{width:13,height:13,color:"var(--warn)",flexShrink:0,marginTop:1}}/>
                  <div className="txt">{m.alert}</div>
                </div>
              )}
              {/* Critical Hold: full banner + mandatory acknowledge */}
              {m.tier==="critical"&&(
                <div className="alert-crit-hold">
                  <div className="hd">
                    <I.shield style={{width:13,height:13,flexShrink:0}}/>
                    <span>CRITICAL HOLD — Do not administer</span>
                    {acked[m.id]&&<span style={{fontSize:11,opacity:.8}}>Acknowledged</span>}
                  </div>
                  <div className="body">
                    <p>{m.alert}</p>
                    <button className={"ack-btn"+(acked[m.id]?" acked":"")} onClick={()=>setAcked(a=>({...a,[m.id]:!a[m.id]}))}>
                      {acked[m.id]?<><I.check style={{width:11,height:11}}/>Acknowledged</>:<><I.alert style={{width:11,height:11}}/>Acknowledge</>}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
          {/* Warning if unacknowledged critical holds remain */}
          {criticalUnacked.length>0&&(
            <div className="unack-warning">
              <I.shield style={{width:13,height:13}}/>
              {criticalUnacked.length} critical hold{criticalUnacked.length>1?"s":""} unacknowledged — order signing is blocked until all critical holds are reviewed.
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ─── Research ─── */
function ResearchPage() {
  return (
    <>
      <div className="ph">
        <div><h1>Evidence & guidelines</h1><div className="ph-sub">Linked to current encounter · ACS workup · Margaret R.</div></div>
      </div>
      <div style={{padding:"18px 26px",display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
        {[
          {t:"2023 ACC/AHA Guideline for STEMI Management",src:"Circulation · 2023",q:"Door-to-balloon < 90 min for primary PCI; ASA 162–325 mg loading dose recommended.",tag:"guideline"},
          {t:"High-sensitivity troponin in 0/1-h algorithm",src:"NEJM · 2022",q:"0/1-h hsTnT algorithm rules out MI in 60% of ED chest pain presentations.",tag:"RCT"},
          {t:"Renal-dosed heparin in CKD stage 3",src:"Chest · 2024",q:"Standard weight-based dosing safe down to CrCl 30; anti-Xa monitoring recommended.",tag:"review"},
          {t:"PARADIGM-HF: ARNI vs ACEi in HFrEF",src:"NEJM · 2014",q:"20% mortality reduction; consider switch post-stabilization in eligible patients.",tag:"RCT"},
        ].map(p=>(
          <div key={p.t} className="panel">
            <div className="panel-h"><h4>{p.t}</h4><span className="pill info"><span className="d"/>{p.tag}</span></div>
            <div className="panel-b">
              <div className="mono" style={{fontSize:11,color:"var(--muted)"}}>{p.src}</div>
              <p className="serif" style={{marginTop:8,fontSize:13,lineHeight:1.55}}>{p.q}</p>
              <div style={{marginTop:10,display:"flex",gap:5}}>
                <button className="btn sm">Open paper →</button>
                <button className="btn sm">Cite in note</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ─── Canvas — UX-5: under "Tools" separator ─── */
function CanvasPage() {
  const [msgs,setMsgs]=useState([{from:"bot",text:"GenUI canvas — describe a component and I'll generate it for the canvas. This workspace is for building custom views, not active patient care."}]);
  const [draft,setDraft]=useState("");
  const [cards,setCards]=useState([]);
  const sugg=["Patient vitals card","Medication reconciliation form","Discharge checklist","Sepsis screening"];
  const generate=(prompt)=>{
    setMsgs(m=>[...m,{from:"user",text:prompt},{from:"bot",text:`Generating "${prompt}"… ready in canvas.`}]);
    setDraft("");
    setCards(c=>[...c,{id:Date.now(),title:prompt,kind:c.length%3}]);
  };
  return (
    <div className="canvas-page">
      <div className="gen-chat">
        <div style={{padding:14,borderBottom:"1px solid var(--line)",display:"flex",gap:9,alignItems:"center"}}>
          <div style={{width:26,height:26,borderRadius:4,background:"var(--accent-soft)",color:"var(--accent-ink)",display:"grid",placeItems:"center",flexShrink:0}}>
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M5 19l3-3M16 8l3-3"/></svg>
          </div>
          <div>
            <div style={{fontWeight:500,fontSize:13}}>GenUI Canvas</div>
            <div style={{color:"var(--muted)",fontSize:11}}>Tool workspace · not for active care</div>
          </div>
        </div>
        <div className="gen-msgs">{msgs.map((m,i)=><div key={i} className={"gmsg "+m.from}>{m.text}</div>)}</div>
        <div className="gen-foot">
          <div className="suggs">{sugg.map(s=><span key={s} className="sugg" onClick={()=>generate(s)}>{s}</span>)}</div>
          <div className="gen-input">
            <input value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Describe a component…" onKeyDown={e=>{if(e.key==="Enter"&&draft.trim())generate(draft.trim());}}/>
            <button onClick={()=>{if(draft.trim())generate(draft.trim());}}><I.send style={{width:13,height:13}}/></button>
          </div>
        </div>
      </div>
      <div className="canvas-stage">
        {cards.length===0?(
          <div className="canvas-empty">
            <div>
              <div style={{width:44,height:44,borderRadius:"50%",background:"var(--surface)",border:"1px dashed var(--line-2)",display:"grid",placeItems:"center",color:"var(--muted-2)",margin:"0 auto 10px"}}><I.plus style={{width:16,height:16}}/></div>
              <div style={{fontSize:14,color:"var(--ink)"}}>Empty canvas</div>
              <div style={{marginTop:3,fontSize:12.5}}>Pick a suggestion or type to generate.</div>
            </div>
          </div>
        ):(
          <div className="canvas-cards">
            {cards.map(c=>(
              <div key={c.id} className="cv-card">
                <div className="ch"><span className="mono">#{c.id.toString().slice(-4)}</span><span style={{fontSize:12}}>{c.title}</span></div>
                <div className="cb">
                  {c.kind===0&&<><div style={{fontSize:10.5,color:"var(--muted)",textTransform:"uppercase",letterSpacing:".08em"}}>Vitals</div><div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:10,marginTop:8}}>{[["HR","118"],["BP","98/62"],["SpO₂","92%"],["RR","24"]].map(([k,v])=><div key={k}><div style={{fontSize:10.5,color:"var(--muted)"}}>{k}</div><div className="mono" style={{fontSize:20}}>{v}</div></div>)}</div></>}
                  {c.kind===1&&<><div style={{fontSize:10.5,color:"var(--muted)",textTransform:"uppercase",letterSpacing:".08em",marginBottom:7}}>Form</div>{["Drug name","Dose","Route","Frequency"].map(l=><div key={l} style={{marginBottom:7}}><div style={{fontSize:10.5,color:"var(--muted)"}}>{l}</div><div style={{height:26,border:"1px solid var(--line)",borderRadius:4,background:"var(--bg)"}}/></div>)}</>}
                  {c.kind===2&&<><div style={{fontSize:10.5,color:"var(--muted)",textTransform:"uppercase",letterSpacing:".08em",marginBottom:7}}>Checklist</div>{["Vitals stable","Pain controlled","Discharge instructions","Follow-up scheduled"].map((l,i)=><label key={l} style={{display:"flex",alignItems:"center",gap:7,padding:"5px 0",fontSize:12.5}}><input type="checkbox" defaultChecked={i<2}/>{l}</label>)}</>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Root ─── */
export default function MedAssist() {
  const [route,setRoute]=useState("triage");
  const [dark,setDark]=useState(false);
  const pages={triage:<TriagePage/>,agents:<AgentsPage/>,radiology:<RadiologyPage/>,vitals:<VitalsPage/>,documentation:<DocumentationPage/>,pharmacy:<PharmacyPage/>,research:<ResearchPage/>,canvas:<CanvasPage/>};
  return (
    <>
      <style>{css}</style>
      <div className={"ma"+(dark?" dark":"")}>
        <Sidebar route={route} setRoute={setRoute}/>
        <div className="ma-main">
          <Topbar route={route} dark={dark} setDark={setDark}/>
          <div className="ma-content" key={route}>{pages[route]}</div>
        </div>
      </div>
    </>
  );
}
