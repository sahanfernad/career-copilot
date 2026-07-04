# Career Copilot — AI Placement Preparation Agent

Career Copilot is a secure multi-agent system built using the Google Agent Development Kit (ADK) that reads a student's resume, identifies skill gaps against a target job description, generates a personalized learning roadmap with concrete projects, and coaches them through mock interviews to track readiness.

## Prerequisites

- Python 3.11 or higher
- [uv](https://astral.sh/uv) - Python package manager
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/career-copilot.git
   cd career-copilot
   ```

2. Set up the environment variables:
   ```bash
   cp .env.example .env
   # Open .env and add your GOOGLE_API_KEY
   ```

3. Install dependencies:
   ```bash
   make install
   ```

4. Launch the local Playground UI:
   - **On macOS/Linux**:
     ```bash
     make playground
     ```
   - **On Windows (PowerShell)**:
     ```powershell
     uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents
     ```
     *(Opens the interactive developer UI at http://localhost:18081)*

---

## Solution Architecture

```mermaid
graph TD
    START[START] --> SecCheck[Security Checkpoint Node]
    SecCheck -->|SECURITY_EVENT| SecError[Security Error Node]
    SecCheck -->|PASS| Orch[Orch/Coordinator Node]
    
    Orch -->|/analyze| PrepResume[Prepare Resume Input]
    PrepResume --> ResumeAgent[Resume & Job Match Agent]
    ResumeAgent --> SaveResume[Save Resume Result]
    SaveResume --> Orch
    
    Orch -->|/roadmap| PrepRoadmap[Prepare Roadmap Input]
    PrepRoadmap --> RoadmapAgent[Learning Roadmap Agent]
    RoadmapAgent --> SaveRoadmap[Save Roadmap Result]
    SaveRoadmap --> Orch
    
    Orch -->|/interview| InterviewCycle[Run Interview Cycle Node]
    InterviewCycle -->|RequestInput| Human[Human User]
    Human -->|Resume Session| InterviewCycle
    InterviewCycle --> Orch
    
    Orch -->|/exit| FinalExit[Handle Exit]
    Orch -->|default| FinalDefault[Handle Default]
    
    FinalExit --> Final[Final Output]
    FinalDefault --> Final
    SecError --> Final

    subgraph MCP Server
        Tools[read_resume_text<br>read_job_description_text<br>get_progress<br>update_progress<br>get_learning_resource_link]
    end
    
    ResumeAgent -.->|Calls MCP| Tools
    RoadmapAgent -.->|Calls MCP| Tools
    InterviewCycle -.->|Calls MCP| Tools
```

---

## How to Run

- **Playground (Interactive UI Mode)**:
  `make playground` (runs on `http://localhost:18081`)
- **FastAPI Server Mode (Production)**:
  `make run` (runs on `http://localhost:8000`)

---

## Sample Test Cases

### Test Case 1: Initial Gap Analysis
* **Input**: Send `/analyze` (or specify paths: `/analyze data/resume.txt data/sample_jd_wso2_backend_intern.txt`).
* **Expected**: The workflow executes the `security_checkpoint` (passes), goes to `orchestrator`, then routes to `resume_agent` via `prepare_resume_input`. The agent calls the MCP server to read `resume.txt` and `sample_jd_wso2_backend_intern.txt`, compares them, and returns a JSON GapReport containing missing skills (FastAPI, Docker, REST APIs, SQL), weak skills, and strong skills (Python, Git).
* **Check**: You will see a formatted **Skill Gap Report** printed in the Playground chat UI, ending with a suggestion to run `/roadmap`.

### Test Case 2: Personalized Roadmap Generation
* **Input**: Send `/roadmap`.
* **Expected**: The workflow routes to `roadmap_agent`. It takes the gaps identified in Test Case 1, reads the local progress store (empty initially), prioritizes the gaps (e.g., FastAPI first, then SQL, Docker), and outputs a sequenced roadmap with resource links and hands-on projects (like "Build a REST API using FastAPI and SQLite").
* **Check**: A detailed **Personalized Learning Roadmap** with prioritized tasks and suggested projects appears in the chat UI.

### Test Case 3: Turn-Based Mock Interview (HITL)
* **Input**: Send `/interview FastAPI`.
* **Expected**: The workflow routes to `run_interview_cycle`. The `interview_agent` is called to generate a technical question about FastAPI. The node yields a `RequestInput(interrupt_id="user_answer")` containing the question and pauses. When you type your answer and hit submit, the node resumes, evaluates your answer, logs the score (0-100) and feedback to the progress store, and displays the score.
* **Check**: The UI first prompts you with the question. Once you respond, it shows the **Mock Interview Evaluation** containing your score and detailed critique.

---

## Troubleshooting

1. **Error: `no agents found` or `extra arguments` when running playground**
   - *Cause*: Incorrect agent directory name or using wildcard `*` expansion on Windows.
   - *Fix*: Ensure you run the exact Windows PowerShell command: `uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents` (where `app` is the actual folder).
2. **Error: `404 Model Not Found` when sending queries**
   - *Cause*: Gemini 1.5 models are retired and return 404.
   - *Fix*: Check your `.env` file and verify `GEMINI_MODEL` is set to `gemini-2.5-flash` or `gemini-2.5-flash-lite`.
3. **Changes to `agent.py` or tools are not showing up in Playground**
   - *Cause*: On Windows, hot-reload does not work reliably due to event loop watcher conflicts.
   - *Fix*: Stop the server using the stop process command (see below) and start a fresh server.

To force-stop any background processes on Windows (PowerShell):
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 18081, 8090 -ErrorAction SilentlyContinue).OwningProcess | Stop-Process -Force
```

---

## Push to GitHub

1. Create a new repo at https://github.com/new
   - Name: `career-copilot`
   - Visibility: Public or Private
   - Do NOT initialize with README (you already have one)

2. In your terminal, navigate into your project folder:
   ```bash
   cd career-copilot
   git init
   git add .
   git commit -m "Initial commit: career-copilot ADK agent"
   git branch -M main
   git remote add origin https://github.com/<your-username>/career-copilot.git
   git push -u origin main
   ```

3. Verify `.gitignore` includes:
   - `.env` (your API key - must NEVER be pushed!)
   - `.venv/`
   - `__pycache__/`
   - `*.pyc`
   - `.adk/`
   - `artifacts/`

---

## Assets

### Cover Page Banner
![Cover Page Banner](assets/cover_page_banner.png)

### Architecture Diagram
![Architecture Diagram](assets/architecture_diagram.png)

---

## Demo Script

The spoken demonstration script for the submission video can be found at [DEMO_SCRIPT.txt](DEMO_SCRIPT.txt).
