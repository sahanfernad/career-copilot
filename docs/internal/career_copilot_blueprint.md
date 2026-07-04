# Career Copilot: AI Placement Preparation Agent
### Full Project Blueprint — Kaggle AI Agents Intensive Vibe Coding Capstone

**Track:** Concierge Agents
**Builder:** Solo
**Timeline:** 12 days

---

## 1. One-Line Pitch

A multi-agent system that reads a student's resume, finds skill gaps against a target job, generates a personalized learning roadmap, and runs mock interviews to track readiness over time — built and tested on the builder's own real placement prep.

---

## 2. The Problem (and why you're the right person to build it)

Students preparing for internships/placements don't get personalized answers to:
- What skills am I actually missing for this role?
- What should I build next to close that gap?
- Am I interview-ready, and where specifically am I weak?

You're living this problem right now (IIT placement year, WSO2 target). The project doubles as a real tool for your own prep — which means your demo video is a true story, not a staged one.

---

## 3. Scope: What We're Building (and deliberately NOT building)

To keep this feasible solo in 12 days, we are cutting from 4 agents to **3 agents + 1 orchestrator**.

| Included ✅ | Cut ❌ (and why) |
|---|---|
| Resume & Job-Match Agent (merged) | Separate "Job Matching Agent" — folded into Resume Agent as a second analysis pass, same value, half the build |
| Learning Roadmap Agent | Live LinkedIn/job-board scraping — ToS risk + not solo-feasible; user pastes JD text instead |
| Interview Coach Agent | Resume parsing from arbitrary formats — support PDF/text only, not scanned images |
| Simple web UI (chat-style) | Multi-user accounts/auth system — single-user local tool is enough for judging |
| Progress tracking (basic) | Persistent database — local JSON/file storage is sufficient |

**Definition of done:** A working end-to-end flow — upload resume + paste JD → see skill gaps → get a roadmap → take a mock interview on a weak area → see it logged as progress.

---

## 4. System Architecture

```
                        ┌─────────────────────┐
                        │   Orchestrator       │
                        │ (coordinates agents, │
                        │  holds session state)│
                        └──────────┬───────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐      ┌──────────▼─────────┐      ┌─────────▼─────────┐
│ Resume & Job-   │      │ Learning Roadmap    │      │ Interview Coach    │
│ Match Agent     │─────▶│ Agent               │─────▶│ Agent              │
│                 │      │                     │      │                    │
│ - Parse resume  │      │ - Takes skill gaps  │      │ - Picks weak topic │
│ - Parse JD text │      │ - Generates ordered │      │ - Asks questions   │
│ - Diff skills   │      │   learning plan     │      │ - Scores answers   │
│ - Output gaps   │      │ - Suggests projects │      │ - Logs result      │
└─────────────────┘      └─────────────────────┘      └────────────────────┘
        │                                                       │
        └───────────────────────┬───────────────────────────────┘
                                 ▼
                      ┌─────────────────────┐
                      │ Progress Store        │
                      │ (local JSON file)     │
                      └─────────────────────┘
```

**Flow:** Resume + JD in → Gap report out → Gap report feeds Roadmap Agent → Roadmap's weak topics feed Interview Coach → Interview results update Progress Store → next session, Roadmap Agent reads progress and adjusts.

This loop (gaps → plan → test → adjust) is the thing that makes it "more than a resume bot" — emphasize this in the pitch.

---

## 5. Agent-by-Agent Detail

### Agent 1: Resume & Job-Match Agent
- **Input:** Resume file (PDF/docx/text), pasted job description text
- **Tasks:**
  1. Extract structured info from resume (skills, projects, experience)
  2. Extract required skills from JD
  3. Diff the two → categorize gaps as "missing," "weak/mentioned but shallow," "strong"
- **Output:** Structured gap report (JSON) passed to Agent 2
- **Tools needed:** Document reading (MCP-based file access), LLM call for extraction/comparison

### Agent 2: Learning Roadmap Agent
- **Input:** Gap report from Agent 1, optional time budget (e.g. "8 weeks")
- **Tasks:**
  1. Order missing/weak skills by priority (foundational → advanced)
  2. Suggest 1 concrete project per major gap (not just "learn X")
  3. Re-generate plan if progress data shows a skill improved
- **Output:** Sequenced roadmap (markdown or structured list)
- **Tools needed:** LLM reasoning, read/write to Progress Store

### Agent 3: Interview Coach Agent
- **Input:** Weakest 1–2 topics from current roadmap
- **Tasks:**
  1. Generate role-relevant interview questions on that topic
  2. Conduct a turn-based Q&A with the user
  3. Score/critique each answer with specific feedback
  4. Write result to Progress Store
- **Output:** Session transcript + score, logged for next roadmap pass
- **Tools needed:** LLM reasoning, Progress Store write access

### Orchestrator
- Routes session state between agents (which agent runs next, what data passes between them)
- Holds the conversation/session context
- This is where the **ADK multi-agent system** concept is demonstrated most directly

---

## 6. Inputs & Data (no Kaggle datasets needed)

This is an agentic system, not a model-training project — inputs are **live, user-provided data**, not static datasets:

| Input | Source |
|---|---|
| Resume | User-uploaded file (your real resume) |
| Job description | User-pasted text (e.g. a real WSO2 backend/SWE internship posting) |
| Skill taxonomy reference (optional) | A small hand-curated list of common backend/AI-role skills, written by you — not scraped |
| Progress history | Generated by the system itself over multiple sessions |

> Drop any "Kaggle dataset" framing from the Writeup — this would read as a mismatch with the assignment to a judge familiar with the course.

---

## 7. Course Concept Mapping (need ≥3, we're targeting 5)

| Concept | Where Demonstrated | How |
|---|---|---|
| **Agent / Multi-agent system (ADK)** | Code | 3 agents + orchestrator built with ADK, each with a distinct role |
| **MCP Server** | Code | Resume/document file access exposed as an MCP tool the Resume Agent calls |
| **Security features** | Code or Video | Resume data processed locally, never persisted beyond the local Progress Store, no third-party storage — explicitly documented |
| **Deployability** | Video | Explain how this could be deployed (e.g. as a local web app or lightweight hosted demo); doesn't need to be live-hosted for judging |
| **Antigravity** | Video | Explain your dev workflow using Antigravity CLI while building this (you already use this tool) |
| Agent skills (CLI) | Code or Video | Optional stretch — only add if time allows after the 3 agents work end-to-end |

---

## 8. Tech Stack (proposed)

- **Agent framework:** Google ADK (multi-agent orchestration)
- **LLM:** via OpenRouter (tool already familiar to you)
- **Document access:** MCP server for local file reading
- **Storage:** Local JSON file for resume parse + progress history
- **Interface:** Simple web UI (chat-style) — Flask/FastAPI backend + minimal HTML/JS frontend, or a Streamlit app if you want speed over polish
- **Video/demo:** Screen recording of the full flow on your real resume + a real WSO2-style JD

---

## 9. Security & Privacy Approach (real, not decorative)

- Resume never leaves local processing except for LLM API calls needed to analyze it
- No cloud database — all storage is local files
- Document explicitly in README: what data is processed, where it's stored, what (if anything) is sent externally and why
- This is a genuine fit for the Concierge track's "keep personal info safe and secure" requirement — not a bolted-on checkbox

---

## 10. Submission Deliverables Checklist

| Deliverable | Requirement | Status |
|---|---|---|
| Kaggle Writeup | ≤2,500 words, title + subtitle + analysis, track selected | ⬜ |
| Cover image | Required for Media Gallery | ⬜ |
| Video | ≤5 min, published to YouTube, covers problem/agents/architecture/demo/build | ⬜ |
| Public project link | Live demo URL, or GitHub repo with setup instructions if no live demo | ⬜ |
| README.md | Problem, solution, architecture, setup instructions, diagrams | ⬜ |
| Code comments | Implementation/design/behavior notes throughout | ⬜ |
| No API keys/secrets in code | Use env vars, .gitignore | ⬜ |

---

## 11. Success Criteria (what "done" looks like for judging)

1. Upload your real resume + paste a real WSO2-style backend internship JD
2. See an accurate, specific gap report (not generic advice)
3. Get a roadmap that references actual gaps, with at least one concrete project suggestion per gap
4. Complete one mock interview round on your weakest flagged topic, get scored feedback
5. Re-run the roadmap step and see it acknowledge the interview result
6. All of this captured cleanly in a 5-minute video with a clear problem → architecture → demo arc

---

## 12. Next Step

Build a day-by-day 12-day plan against this blueprint, sequencing: orchestrator + Agent 1 first (since 2 and 3 depend on its output), then Agent 2, then Agent 3, then UI polish, then video/writeup — with buffer days for the things that always slip.
