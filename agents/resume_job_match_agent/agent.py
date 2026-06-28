"""
Part 1 — Agent 1: Resume & Job-Match Agent
---------------------------------------------
Course concept demonstrated: Agent (ADK), the foundational building block
before Part 4 adds the multi-agent / MCP layer on top.

Input (handled OUTSIDE this file, by utils/document_reader.py):
    resume_text — plain text extracted from the resume
    jd_text     — pasted job description text

This agent's only job: given resume_text + jd_text, return a structured
gap report as JSON with three categories — missing, weak, strong — per
the blueprint's spec. No file I/O, no other tools yet; that keeps Part 1
scoped and testable in isolation.

Test it today with:
    adk web agents/resume_job_match_agent
and paste in resume_text + jd_text via the local web UI ADK spins up.
We wire this into orchestrator.py programmatically in Part 2, once
there's a second agent to actually route to.
"""

from google.adk.agents.llm_agent import Agent

GAP_REPORT_INSTRUCTION = """\
You are the Resume & Job-Match Agent for Career Copilot, a placement-prep \
tool for a software engineering student.

You will be given two pieces of text in the user's message:
1. RESUME: the candidate's resume content
2. JOB DESCRIPTION: the target role's job description

Your task:
1. Extract the candidate's skills, projects, and experience from the resume.
2. Extract the required/preferred skills from the job description.
3. Compare the two and categorize every JD skill into exactly one bucket:
   - "missing": not mentioned anywhere in the resume
   - "weak": mentioned in the resume but shallow — e.g. listed once with no \
project/experience backing it up, or used in a toy/course-only context
   - "strong": clearly demonstrated through a real project or experience

Respond with ONLY valid JSON in exactly this shape, no markdown fences, no \
preamble, no commentary:

{
  "missing": ["skill name", "..."],
  "weak": [
    {"skill": "skill name", "reason": "why it's weak, one sentence"}
  ],
  "strong": [
    {"skill": "skill name", "evidence": "which resume project/experience proves it"}
  ],
  "summary": "2-3 sentence plain-English summary of overall fit"
}

Be specific and honest. Do not pad the "strong" list to be encouraging — \
the next agent in this pipeline builds a learning roadmap directly from \
your "missing" and "weak" lists, so accuracy here matters more than tact.
"""

root_agent = Agent(
    model="gemini-flash-latest",
    name="resume_job_match_agent",
    description=(
        "Diffs a candidate's resume against a target job description and "
        "produces a categorized skill-gap report (missing/weak/strong)."
    ),
    instruction=GAP_REPORT_INSTRUCTION,
)
