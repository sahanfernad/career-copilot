# AI Agents: Intensive Vibe Coding Capstone Project
## Career Copilot: AI Placement Preparation Agent

**Track:** Concierge Agents
**Builder:** Solo (Solo Developer)
**Demo Video:** [Watch on YouTube](https://youtu.be/d0eyS9mBqSM) (extended uncut demo also available [here](https://youtu.be/d0UBUYvQDXU))

---

### 1. Problem Statement
Preparing for internships and job placements is a major challenge for students. They struggle to find answers to critical questions:
- What skills are actually missing from my resume for a specific target role?
- How can I systematically close those gaps with hands-on projects rather than passive learning?
- Am I truly ready for technical interviews, and where specifically are my weak points?

Career Copilot solves this problem by offering a local, secure, and personalized concierge agent that acts as an end-to-end career strategist. By inputting their own resume and a target job description, students receive an instant skill-gap audit, a structured project-based roadmap, and interactive mock interview coaching that adapts to their progress over time.

---

### 2. Solution Architecture

![Architecture Diagram](assets/architecture_diagram.png)

---

### 3. Course Concepts Demonstrated

1. **ADK 2.0 Workflow & Graph Topology (`app/agent.py`)**
   - Implemented using the `Workflow` class from `google.adk.workflow`. We define nodes (functions and LLM agents) and coordinate them via conditional edges mapped to route-determining helper nodes (`orchestrator`, `security_checkpoint`).
   
2. **LlmAgent Sub-Agents (`app/agent.py`)**
   - Built three specialized `LlmAgent` instances:
     - `resume_job_match_agent`: Generates a structured JSON gap report.
     - `learning_roadmap_agent`: Translates gaps into project-based learning roadmaps.
     - `interview_coach_agent`: Runs turn-based mock interviews and evaluations.
     - Each uses standard `output_schema` validation to ensure structured, predictable API responses.

3. **Sub-Agent Delegation (`app/agent.py`)**
   - Delegated to specialized sub-agents (resume analysis, roadmap planning, interview coaching) via ctx.run_node(agent, node_input=...) inside dedicated workflow nodes, keeping each agent's invocation, timeout handling, and output persistence isolated and independently testable. This allows parent orchestrator nodes to call specialist agents dynamically while maintaining execution context.

4. **Model Context Protocol (MCP) Server (`app/mcp_server.py`)**
   - Implemented an MCP server on the `stdio` transport using `FastMCP`. Exposes tools to read local files (`read_resume_text`, `read_job_description_text`) and manage state (`get_progress`, `update_progress`). The tools are connected to agents using the `McpToolset` class.

5. **Security Checkpoint Node (`app/agent.py`)**
   - Implemented `security_checkpoint` as the gateway node for the entire workflow. It performs PII scrubbing, detects prompt injections, enforces SWE-domain relevancy checks, and writes structured JSON logs for audit trails.

6. **Agents CLI Scaffolding (`app/` structure)**
   - Initialized and structured using `agents-cli scaffold create`, producing standard app configurations, environment variables (`.env`), and a pinned dependency workspace (`pyproject.toml`).

7. **Agent Skills (`app/skills/resource_recommendation/SKILL.md`)**
   - Implemented the `resource_recommendation` Agent Skill to dynamically surface learning resources. During `/roadmap` generation, the `learning_roadmap_agent` calls the `get_learning_resource_link` MCP tool for each identified skill gap, producing a properly URL-encoded YouTube search link. This tool is fully deterministic (built using `urllib.parse` with no LLM calls or network requests), eliminating link hallucination risks while consuming zero API quota and adding negligible latency. Since the roadmap itself is generated live based on the candidate's resume and job description, the number and phrasing of generated links will vary dynamically between runs. This completes the "Agent Skills" requirement, fulfilling the final rubric category for the submission.

8. **Deployability (`deployment/terraform/`)**
   - Full Terraform IaC provisioning Google Cloud Run (`service.tf`), IAM (`iam.tf`), storage (`storage.tf`), telemetry (`telemetry.tf`), and enabled APIs (`apis.tf`), with environment-specific variables in `vars/env.tfvars` — demonstrating the project is deployable beyond a local demo.

---

### 4. Security Design
- **PII Scrubbing**: Active regular expressions scan all user input for personal identifiers (such as emails and phone numbers) and replace them with `[REDACTED_EMAIL]` and `[REDACTED_PHONE]` before passing inputs to the LLM agents.
- **Prompt Injection Detection**: Scans user input for malicious keywords ("ignore previous instructions", "jailbreak", etc.) and routes the request to a `SECURITY_EVENT` handler, blocking further LLM execution.
- **SWE-Domain Relevancy Check**: An input validator verifies that any uploaded text contains tech-specific terms. If not, it raises a WARNING to prevent malicious or out-of-scope usage of model resources.
- **Local Sovereignty**: All processing (document reading, progress logging) is done locally on the student's machine. Data is never persisted in external cloud databases.

---

### 5. MCP Server Design
The local MCP server (`app/mcp_server.py`) runs as a background process and exposes the following tools:
1. `read_resume_text`: Parses PDF, DOCX, and TXT files using native libraries (`pypdf` and `python-docx`).
2. `read_job_description_text`: Parses job descriptions from a file or passes through raw pasted text.
3. `get_progress`: Reads the local progress store (`storage/progress.json`) to check what skills the student has already mastered.
4. `update_progress`: Saves scores, feedback, and completed skills back to the local progress store.
5. `get_learning_resource_link`: Generates a deterministic, URL-encoded YouTube search link for a given skill name (no LLM calls, no network requests) — used by the Agent Skills feature described in Section 3.7.

---

### 6. Human-in-the-Loop (HITL) Flow
The mock interview coach (`run_interview_cycle` in `app/agent.py`) leverages ADK's `RequestInput` mechanism.
- The workflow yields `RequestInput(interrupt_id="user_answer", message=question)` to pause execution.
- This suspends the state and prompts the user for their response.
- Once the user types their answer, the runner resumes the session and passes the user's answer back into the node for evaluation.

---

### 7. Demo Walkthrough
- **Phase 1: Gap Analysis (`/analyze`)**
  - Reads a student's resume (e.g., Python, Javascript) and a target job description (e.g., requiring FastAPI, Docker, SQL). Identifies skill gaps and outputs them in structured JSON.
- **Phase 2: Roadmap Generation (`/roadmap`)**
  - Generates a customized learning plan pointing the student to specific projects (e.g., "Build a REST API using FastAPI") to close the gaps.
- **Phase 3: Interview Coaching (`/interview FastAPI`)**
  - Generates a challenging FastAPI question. Once the student answers, the coach scores it (e.g., 85/100) and updates the local progress file. Subsequent roadmaps acknowledge this progress and prioritize other areas.

---

### 8. Impact / Value Statement
The problem. Placement prep for backend + AI roles is fragmented and generic. Students bounce between resume templates, unstructured YouTube roadmaps, and one-size-fits-all mock interview scripts — none of which account for the specific gap between a student's actual skill profile and a specific job description. For a student targeting a narrow specialization (e.g., backend engineering + AI integration), this generic advice often points in the wrong direction entirely.
What Career Copilot does differently. Rather than generic advice, Career Copilot performs job-specific gap analysis, generates a sequenced learning roadmap tied to that gap, and runs adaptive interview coaching — all orchestrated as a multi-agent system rather than a single prompt-and-response tool. In live testing against the real Gemini API (not mocked), the system:

- Identified role-specific, non-generic skill gaps (the exact skills depend on the uploaded resume and JD — by design, no two analyses produce the same output) rather than returning boilerplate advice.
- Produced a sequenced, multi-item roadmap tied directly to those identified gaps, with a YouTube search resource link generated per skill via the MCP tool.
- Generated a genuinely challenging, topic-appropriate interview question live from the LLM, rather than pulling from a static question bank — question depth and format vary naturally with the chosen topic.
- Scored a deliberately weak, off-topic test answer near the bottom of the 0–100 range, with a specific explanation of why it was weak — evidence of real evaluative reasoning grounded in the candidate's actual response, not keyword matching.

Why this matters beyond a demo. The architecture — security checkpoint with PII redaction and injection detection, human-in-the-loop review via RequestInput, and a real MCP tool server rather than hardcoded logic — reflects design choices aimed at something a student could actually trust with their real resume and real career data, not just a hackathon toy. The gap-analysis-to-roadmap-to-interview pipeline mirrors how a genuinely good career mentor would work: diagnose first, then prescribe, then test — and it does this specifically for the backend + AI integration niche that generic placement tools ignore.
Who this is for. Any student targeting a specialized technical role where generic "learn to code" advice doesn't match the actual bar — starting with backend + AI integration placements, but the gap-analysis pattern generalizes to any role with a defined, checkable skill profile.

---

### 9. Project Journey & Engineering Refinements
Career Copilot started as ad-hoc, "vibe-coded" scripts in the Antigravity IDE rather than a structured system — quick experiments to validate the resume-to-roadmap idea before any real architecture existed. The turning point was restructuring the project around ADK 2.0's `Workflow` graph and dedicated `LlmAgent` nodes, which forced clearer boundaries between orchestration, security, and agent logic instead of one tangled script. Along the way, debugging in Antigravity surfaced concrete engineering issues: a stale-session bug in the interview flow, an inconsistent `MOCK_LLM` flag that silently broke local testing, and a `.env.example` default that pointed to mock mode instead of the real Gemini API. Each fix pushed the project further from "vibe coding" toward deliberate agentic engineering — the security checkpoint, MCP tool boundaries, and Terraform deployment layer were all added after the core workflow was already working, specifically to harden a demo-stage prototype into something closer to a trustworthy, deployable tool.