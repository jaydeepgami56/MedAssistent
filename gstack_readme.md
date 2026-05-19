# gstack Skills Reference

gstack is a suite of Claude Code slash commands that extend your coding agent with browser automation, design review, deployment workflows, security auditing, and more. Each skill is invoked as `/skill-name` inside Claude Code.

---

## Table of Contents

1. [Browser & QA](#browser--qa)
2. [Design](#design)
3. [Planning & Review](#planning--review)
4. [Ship & Deploy](#ship--deploy)
5. [Security & Safety](#security--safety)
6. [Debugging & Quality](#debugging--quality)
7. [Setup & Configuration](#setup--configuration)
8. [Agent Collaboration](#agent-collaboration)
9. [Session Management](#session-management)
10. [Utilities](#utilities)

---

## Browser & QA

### `/browse`
Fast headless browser for QA testing and site dogfooding. Navigate any URL, interact with elements, verify page state, diff before/after actions, take annotated screenshots, check responsive layouts, test forms and uploads, handle dialogs, and assert element states. ~100ms per command.

**Use when:** testing a site, verifying a deployment, dogfooding a user flow, or taking bug evidence screenshots.

---

### `/gstack`
Alias for `/browse`. Same fast headless browser for QA testing and site inspection. Navigate pages, interact with elements, verify state, diff before/after, and capture bug evidence.

---

### `/open-gstack-browser` / `/connect-chrome`
Launch GStack Browser — an AI-controlled Chromium instance with a sidebar extension baked in. Opens a **visible** browser window where you can watch every action in real time. The sidebar shows a live activity feed and chat. Anti-bot stealth built in.

**Use when:** you want to observe browser automation live, or when headless tools are blocked by anti-bot measures.

---

### `/qa`
Systematically QA test a web application **and fix bugs found**. Runs QA testing, then iteratively fixes bugs in source code, committing each fix atomically and re-verifying with the browser.

**Use when:** "qa", "test this site", "find bugs", "test and fix", or "fix what's broken".

---

### `/qa-only`
Report-only QA testing. Systematically tests a web application and produces a structured report with a health score, screenshots, and repro steps — **never modifies any code**.

**Use when:** you want a bug report without automated fixes. Use `/qa` for the full test-fix-verify loop.

---

### `/scrape`
Pull data from a web page. First call on a new intent prototypes the flow via browser primitives and returns JSON. Subsequent calls on a matching intent route to a codified browser skill and return in ~200ms. Read-only.

**Use when:** "scrape", "get data from", "extract from page". For mutating flows (form fills, clicks, submissions), use `/automate`.

---

### `/setup-browser-cookies`
Import cookies from your real Chromium browser into the headless browse session. Opens an interactive picker UI where you select which cookie domains to import.

**Use when:** you need to QA test authenticated pages. Run this before `/qa` or `/browse` on protected routes.

---

### `/skillify`
Codify the most recent successful `/scrape` flow into a permanent browser skill on disk. Future `/scrape` calls with the same intent run the codified script in ~200ms instead of re-driving the page. Walks back through the conversation, synthesizes `script.ts + script.test.ts + fixture`, runs the test in a temp dir, and saves it.

**Use when:** a scrape flow works and you want it fast and reliable on every future run.

---

## Design

### `/design-consultation`
Design consultation: understands your product, researches the landscape, proposes a complete design system (aesthetic, typography, color, layout, spacing, motion), and generates font + color preview pages. Creates `DESIGN.md` as your project's design source of truth.

**Use when:** starting a new project, rebranding, or you want a coherent design system from scratch.

---

### `/design-shotgun`
Generate multiple AI design variants, open a comparison board, collect structured feedback, and iterate. Standalone design exploration you can run anytime.

**Use when:** "explore designs", "show me options", "design variants", "visual brainstorm", or "I don't like how this looks".

---

### `/design-html`
Design finalization: generates production-quality HTML/CSS. Works with approved mockups from `/design-shotgun`, CEO plans from `/plan-ceo-review`, design review context from `/plan-design-review`, or from scratch with a description. Text reflows, heights are computed, layouts are dynamic.

**Use when:** you have an approved design and need it turned into real, production-ready HTML/CSS.

---

### `/design-review`
Designer's eye QA: finds visual inconsistency, spacing issues, hierarchy problems, AI slop patterns, and slow interactions — then **fixes them**. Iteratively fixes issues in source code, committing each fix atomically and re-verifying with before/after screenshots.

**Use when:** a feature is built and you want visual polish. For plan-mode design review (before implementation), use `/plan-design-review`.

---

## Planning & Review

### `/autoplan`
Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially with auto-decisions using 6 decision principles. Surfaces taste decisions (close approaches, borderline scope, codex disagreements) at a final approval gate. One command, fully reviewed plan out.

**Use when:** you want a comprehensive multi-lens plan review in one shot.

---

### `/plan-ceo-review`
CEO/founder-mode plan review. Rethink the problem, find the 10-star product, challenge premises, expand scope when it creates a better product.

**Four modes:**
- `SCOPE EXPANSION` — dream big
- `SELECTIVE EXPANSION` — hold scope + cherry-pick expansions
- `HOLD SCOPE` — maximum rigor
- `SCOPE REDUCTION` — strip to essentials

**Use when:** "ceo review", "product review", "challenge my plan", or "is this the right thing to build?"

---

### `/plan-eng-review`
Eng manager-mode plan review. Lock in the execution plan — architecture, data flow, diagrams, edge cases, test coverage, performance. Walks through issues interactively with opinionated recommendations.

**Use when:** "review the architecture", "engineering review", or "lock in the plan".

---

### `/plan-design-review`
Designer's eye plan review — interactive, like CEO and Eng review. Rates each design dimension 0-10, explains what would make it a 10, then fixes the plan to get there. Works in plan mode.

**Use when:** "review the design plan" or "design critique". For live site visual audits, use `/design-review` instead.

---

### `/plan-devex-review`
Interactive developer experience plan review. Explores developer personas, benchmarks against competitors, designs magical moments, and traces friction points before scoring.

**Three modes:** DX EXPANSION (competitive advantage), DX POLISH (bulletproof every touchpoint), DX TRIAGE (critical gaps only).

**Use when:** "devex review", "developer experience audit", or "dx critique".

---

### `/review`
Pre-landing PR review. Analyzes diff against the base branch for SQL safety, LLM trust boundary violations, conditional side effects, and other structural issues. Pass/fail gate with detailed findings.

**Use when:** "review this PR", "code review", "pre-landing review", or "check my diff". Proactively runs before merging.

---

### `/codex`
OpenAI Codex CLI wrapper — three modes:
- **Code review:** independent diff review via `codex review` with pass/fail gate
- **Challenge:** adversarial mode that tries to break your code
- **Consult:** ask codex anything with session continuity for follow-ups

The "200 IQ autistic developer" second opinion.

**Use when:** "codex review", "challenge this code", or "get a second opinion".

---

### `/office-hours`
YC Office Hours — two modes:
- **Startup mode:** six forcing questions that expose demand reality, status quo, desperate specificity, narrowest wedge, observation, and future-fit
- **Builder mode:** design thinking brainstorming for side projects, hackathons, learning, and open source

Saves a design doc.

**Use when:** "office hours", "brainstorm", "validate my idea", or "I'm building a side project".

---

## Ship & Deploy

### `/ship`
Ship workflow: detect + merge base branch, run tests, review diff, bump VERSION, update CHANGELOG, commit, push, create PR. Full end-to-end from working code to open PR.

**Use when:** "ship", "deploy", "push to main", "create a PR", "merge and push", or "get it deployed".

---

### `/land-and-deploy`
Land and deploy workflow. Merges the PR, waits for CI and deploy, verifies production health via canary checks. Takes over after `/ship` creates the PR.

**Use when:** "merge", "land", "deploy", "merge and verify", "land it", or "ship it to production".

---

### `/canary`
Post-deploy canary monitoring. Watches the live app for console errors, performance regressions, and page failures using the browse daemon. Takes periodic screenshots, compares against pre-deploy baselines, and alerts on anomalies.

**Use when:** "monitor deploy", "canary", "post-deploy check", "watch production", or "verify deploy".

---

### `/benchmark`
Performance regression detection using the browse daemon. Establishes baselines for page load times, Core Web Vitals, and resource sizes. Compares before/after on every PR. Tracks performance trends over time.

**Use when:** "performance", "benchmark", "page speed", "lighthouse", "web vitals", "bundle size", or "load time".

---

### `/benchmark-models`
Cross-model benchmark for gstack skills. Runs the same prompt through Claude, GPT (via Codex CLI), and Gemini side-by-side — compares latency, tokens, cost, and optionally quality via LLM judge.

**Use when:** "which model is best for this?", "compare models", or "benchmark models".

---

### `/landing-report`
Read-only queue dashboard for workspace-aware ship. Shows which VERSION slots are currently claimed by open PRs, which sibling Conductor workspaces have WIP work likely to ship soon, and what slot `/ship` would pick next. No mutations — just a snapshot.

**Use when:** "landing report", "what's in the queue", or "show the ship queue".

---

### `/setup-deploy`
Configure deployment settings for `/land-and-deploy`. Detects your deploy platform (Fly.io, Render, Vercel, Netlify, Heroku, GitHub Actions, custom), production URL, health check endpoints, and deploy status commands. Writes configuration to `CLAUDE.md` so all future deploys are automatic.

**Use when:** "setup deploy", "configure deployment", or before your first `/land-and-deploy`.

---

### `/document-release`
Post-ship documentation update. Reads all project docs, cross-references the diff, updates `README` / `ARCHITECTURE` / `CONTRIBUTING` / `CLAUDE.md` to match what shipped, polishes `CHANGELOG` voice, cleans up TODOs, and optionally bumps VERSION.

**Use when:** "update the docs", "sync documentation", or "post-ship docs".

---

## Security & Safety

### `/cso`
Chief Security Officer mode. Infrastructure-first security audit: secrets archaeology, dependency supply chain, CI/CD pipeline security, LLM/AI security, skill supply chain scanning, plus OWASP Top 10, STRIDE threat modeling, and active verification.

**Two modes:** daily (zero-noise, 8/10 confidence gate) and comprehensive (full audit).

**Use when:** "security audit", "cso review", "check for secrets", or "threat model".

---

### `/careful`
Safety guardrails for destructive commands. Warns before `rm -rf`, `DROP TABLE`, force-push, `git reset --hard`, `kubectl delete`, and similar destructive operations. User can override each warning.

**Use when:** touching prod, debugging live systems, or working in a shared environment. Use when asked to "be careful" or "safety mode".

---

### `/freeze`
Restrict file edits to a specific directory for the session. Blocks `Edit` and `Write` outside the allowed path.

**Use when:** debugging to prevent accidentally "fixing" unrelated code, or when you want to scope changes to one module.

---

### `/guard`
Full safety mode: destructive command warnings + directory-scoped edits. Combines `/careful` (warns before destructive ops) with `/freeze` (blocks edits outside a specified directory). Maximum safety.

**Use when:** "guard mode", "full safety", or working in production environments.

---

### `/unfreeze`
Clear the freeze boundary set by `/freeze`, allowing edits to all directories again.

**Use when:** "unfreeze", "unlock edits", "remove freeze", or "allow all edits".

---

## Debugging & Quality

### `/investigate`
Systematic debugging with root cause investigation. Four phases: investigate, analyze, hypothesize, implement.

**Iron Law:** no fixes without root cause.

**Use when:** "debug this", "fix this bug", "why is this broken", "investigate this error", or "root cause analysis". Proactively suggested instead of ad-hoc debugging.

---

### `/health`
Code quality dashboard. Wraps existing project tools (type checker, linter, test runner, dead code detector, shell linter), computes a weighted composite 0-10 score, and tracks trends over time.

**Use when:** "health check", "code quality", "how healthy is the codebase", "run all checks", or "quality score".

---

### `/retro`
Weekly engineering retrospective. Analyzes commit history, work patterns, and code quality metrics with persistent history and trend tracking. Team-aware: breaks down per-person contributions with praise and growth areas.

**Use when:** "weekly retro", "what did we ship", or "engineering retrospective".

---

## Setup & Configuration

### `/setup-gbrain`
Set up gbrain for this coding agent: install the CLI, initialize a local PGLite or Supabase brain, register MCP, capture per-remote trust policy. One command from zero to "gbrain is running and this agent can call it."

**Use when:** "setup gbrain", "connect gbrain", "start gbrain", "install gbrain", or "configure gbrain".

---

### `/gstack-upgrade`
Upgrade gstack to the latest version. Detects global vs vendored install, runs the upgrade, and shows what's new.

**Use when:** "upgrade gstack", "update gstack", or "get latest version".

---

### `/plan-tune`
Self-tuning question sensitivity + developer psychographic for gstack (v1: observational). Review which `AskUserQuestion` prompts fire across gstack skills, set per-question preferences (never-ask / always-ask / ask-only-for-one-way), and inspect the dual-track profile.

**Use when:** "tune gstack", "stop asking me X", or "adjust question sensitivity".

---

## Agent Collaboration

### `/pair-agent`
Pair a remote AI agent with your browser. One command generates a setup key and prints instructions the other agent can follow to connect. Works with OpenClaw, Hermes, Codex, Cursor, or any agent that can make HTTP requests. The remote agent gets its own tab with scoped access.

**Use when:** "pair agent", "connect another agent", or coordinating multi-agent workflows.

---

## Session Management

### `/context-save`
Save working context. Captures git state, decisions made, and remaining work so any future session can pick up without losing a beat.

**Use when:** "save progress", "save state", "context save", or "save my work". Pair with `/context-restore` to resume later.

---

### `/context-restore`
Restore working context saved earlier by `/context-save`. Loads the most recent saved state (across all branches by default) so you can pick up where you left off — even across Conductor workspace handoffs.

**Use when:** "resume", "restore context", "where was I", or "pick up where I left off".

---

## Utilities

### `/learn`
Manage project learnings. Review, search, prune, and export what gstack has learned across sessions.

**Use when:** "what have we learned", "show learnings", "prune stale learnings", or "export learnings". Proactively suggested when you wonder "didn't we fix this before?"

---

### `/make-pdf`
Turn any markdown file into a publication-quality PDF. Proper 1-inch margins, intelligent page breaks, page numbers, cover pages, running headers, curly quotes and em dashes, clickable TOC, diagonal DRAFT watermark.

**Use when:** "make a PDF", "export to PDF", or "turn this into a document".

---

## Quick Reference

| Category | Skills |
|----------|--------|
| **Browser** | `/browse`, `/gstack`, `/open-gstack-browser`, `/scrape`, `/skillify` |
| **QA** | `/qa`, `/qa-only`, `/setup-browser-cookies` |
| **Design** | `/design-consultation`, `/design-shotgun`, `/design-html`, `/design-review` |
| **Planning** | `/autoplan`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/plan-devex-review`, `/office-hours` |
| **Code Review** | `/review`, `/codex` |
| **Ship** | `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/landing-report`, `/document-release` |
| **Security** | `/cso`, `/careful`, `/freeze`, `/guard`, `/unfreeze` |
| **Debug** | `/investigate`, `/health`, `/retro` |
| **Setup** | `/setup-deploy`, `/setup-gbrain`, `/setup-browser-cookies`, `/gstack-upgrade`, `/plan-tune` |
| **Agents** | `/pair-agent` |
| **Session** | `/context-save`, `/context-restore` |
| **Utilities** | `/learn`, `/make-pdf` |

---

> All skills are invoked as `/skill-name` inside Claude Code. Use `/browse` (not `mcp__claude-in-chrome__*` tools) for all web browsing.
