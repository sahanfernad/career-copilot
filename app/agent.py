import asyncio
import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from google.adk.workflow import Workflow, START, node, FunctionNode, Edge
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

from app.config import config

# Setup security logging
logger = logging.getLogger("career-copilot-security")

# Resolve MCP server absolute path
mcp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server.py"))

# MCP connection setup
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[mcp_path]
        )
    )
)

# --- Pydantic Schemas ---

class WeakSkill(BaseModel):
    skill: str
    reason: str

class StrongSkill(BaseModel):
    skill: str
    evidence: str

class GapReport(BaseModel):
    missing: List[str] = Field(default_factory=list)
    weak: List[WeakSkill] = Field(default_factory=list)
    strong: List[StrongSkill] = Field(default_factory=list)
    summary: str = ""

class RoadmapItem(BaseModel):
    skill: str
    priority: str  # "High", "Medium", "Low"
    resource_or_method: str
    suggested_project: str
    resource_link: Optional[str] = None

class LearningRoadmap(BaseModel):
    items: List[RoadmapItem] = Field(default_factory=list)
    summary: str = ""

class InterviewFeedback(BaseModel):
    question: str
    user_answer: str
    feedback: str
    score: int

# --- Sub-Agents ---

resume_agent = LlmAgent(
    name="resume_job_match_agent",
    model=config.model,
    instruction="""You are the Resume & Job-Match Agent for Career Copilot.
Your task is to analyze the candidate's resume and a target job description.
Identify the skill gaps and categorize them into:
1. "missing": skills not mentioned at all in the resume
2. "weak": skills mentioned but with shallow experience (e.g. no projects/experience backing them, or course-only context)
3. "strong": skills clearly backed by projects or work experience

Output MUST be a JSON object conforming to the GapReport schema. Be specific and honest.
""",
    output_schema=GapReport,
    tools=[mcp_toolset],
)

roadmap_agent = LlmAgent(
    name="learning_roadmap_agent",
    model=config.model,
    instruction="""You are the Learning Roadmap Agent for Career Copilot.
Your task is to take the GapReport (missing & weak skills) and output a personalized, sequenced learning roadmap.
For each gap, suggest 1 concrete hands-on project to build and a recommended learning resource.
Read the progress store (using get_progress tool) to adjust your recommendations based on what's already completed.
For each roadmap item, call the `get_learning_resource_link` tool with the skill name as input, and populate the returned URL string in the `resource_link` field of that RoadmapItem.
IMPORTANT: Pass only the bare, clean skill/topic name as input to `get_learning_resource_link` (e.g., use "Docker containerization" or "Java", NOT "Docker containerization tutorial" or "Java course"). Do not append suffix words like "tutorial", "course", "guide", or similar, since the tool appends its own suffix.
Output MUST be a JSON object conforming to the LearningRoadmap schema.
""",
    output_schema=LearningRoadmap,
    tools=[mcp_toolset],
)

interview_agent = LlmAgent(
    name="interview_coach_agent",
    model=config.model,
    instruction="""You are the Interview Coach Agent for Career Copilot.
Your task is to generate technical interview questions for a specific topic, evaluate the user's response, and score it.
Output MUST be a JSON object conforming to the InterviewFeedback schema.
""",
    output_schema=InterviewFeedback,
    tools=[mcp_toolset],
)

# --- Shared interview question fallback ---

def _interview_question_fallback(topic: str) -> str:
    """Hardcoded questions — used only when the LLM call fails or times out."""
    is_generic = topic.strip().lower() in ("general swe", "")
    topic_clause = f" in {topic}" if not is_generic else ""
    if "sql" in topic.lower() or "database" in topic.lower():
        return f"What is the difference between a primary key and a foreign key in {topic}, and how do they establish relationships?"
    elif "docker" in topic.lower() or "container" in topic.lower():
        return "Explain the difference between a Docker Image and a Docker Container."
    elif is_generic:
        return "What is the difference between path parameters and query parameters in a REST API, and when should you use each?"
    else:
        return f"What is the difference between path parameters and query parameters{topic_clause}, and when should you use each?"


# --- Mock Agent Nodes (for offline/free testing) ---

def mock_resume_agent_node(node_input: str) -> GapReport:
    return GapReport(
        missing=["FastAPI", "Docker", "SQL"],
        weak=[
            WeakSkill(skill="REST APIs", reason="Mentioned in resume but no projects shown"),
            WeakSkill(skill="Git", reason="Basic usage only, no advanced workflow")
        ],
        strong=[
            StrongSkill(skill="Python", evidence="Completed 3 python projects and SWE internship"),
            StrongSkill(skill="HTML/CSS", evidence="Built portfolio website")
        ],
        summary="Candidate has strong Python fundamentals but lacks backend framework (FastAPI) and deployment (Docker, SQL) skills required for the internship."
    )

def mock_roadmap_agent_node(node_input: str) -> LearningRoadmap:
    import json as _json
    from app.mcp_server import get_learning_resource_link
    # Parse completed_skills from the input so we can skip already-tested skills
    completed = []
    try:
        if "COMPLETED SKILLS" in node_input:
            cs_section = node_input.split("COMPLETED SKILLS:")[1].strip()
            completed = [s.lower() for s in _json.loads(cs_section)]
    except Exception:
        pass

    all_items = [
        RoadmapItem(
            skill="FastAPI",
            priority="High",
            resource_or_method="FastAPI Tutorial (official docs)",
            suggested_project="Build a REST API for a Bookstore with FastAPI",
            resource_link=get_learning_resource_link("FastAPI")
        ),
        RoadmapItem(
            skill="SQL & Databases",
            priority="High",
            resource_or_method="SQLAlchemy & SQLite documentation",
            suggested_project="Integrate Bookstore REST API with SQLite database using SQLAlchemy",
            resource_link=get_learning_resource_link("SQL & Databases")
        ),
        RoadmapItem(
            skill="Docker",
            priority="Medium",
            resource_or_method="Docker Getting Started Guide",
            suggested_project="Containerize the Bookstore REST API using Docker",
            resource_link=get_learning_resource_link("Docker")
        )
    ]

    # Downgrade priority for skills already tested (score >= 70 → completed)
    items = []
    for item in all_items:
        if item.skill.lower() in completed or any(c in item.skill.lower() for c in completed):
            items.append(RoadmapItem(
                skill=item.skill,
                priority="Low (already practiced)",
                resource_or_method=item.resource_or_method,
                suggested_project=item.suggested_project,
                resource_link=item.resource_link
            ))
        else:
            items.append(item)

    return LearningRoadmap(
        items=items,
        summary="A learning plan focusing on backend fundamentals (FastAPI), databases (SQL), and deployment (Docker). Skills already tested in mock interviews are deprioritized."
    )

async def mock_interview_agent_node(node_input: str) -> InterviewFeedback:
    # Check if evaluating an answer
    if "Evaluate" in node_input or "User Answer:" in node_input:
        # Extract Topic, Question, and User Answer
        topic_match = re.search(r"Topic:\s*(.*)", node_input, re.IGNORECASE)
        question_match = re.search(r"Question:\s*(.*)", node_input, re.IGNORECASE)
        answer_match = re.search(r"User Answer:\s*(.*)", node_input, re.IGNORECASE)
        
        topic = topic_match.group(1).strip() if topic_match else "General SWE"
        question = question_match.group(1).strip() if question_match else "Explain your understanding of this topic."
        user_answer = answer_match.group(1).strip() if answer_match else ""
        
        # Clean up user answer
        user_answer_clean = user_answer.lower().strip("[]()\"' ")
        
        # Determine score and detailed feedback based on response quality
        if not user_answer_clean or user_answer_clean in ["no", "no idea", "i don't know", "dont know", "skip", "none", "na", "n/a", "."]:
            score = 0
            feedback = (
                "Your answer is empty or indicates you don't know the topic. "
                "For a Software Engineering role at WSO2, you should be able to explain core backend concepts. "
                "Here is the correct explanation:\n\n"
                "- **Path Parameters**: Part of the URL path (e.g., `/items/{item_id}`). Used to identify a specific resource. They are required.\n"
                "- **Query Parameters**: Key-value pairs appended after the `?` in the URL (e.g., `/items?limit=10`). Used for filtering, sorting, or optional pagination. They are optional by default.\n\n"
                "Please review this and try another topic or attempt to answer again!"
            )
        elif len(user_answer_clean) < 15:
            score = 30
            feedback = (
                f"Your answer '{user_answer}' is too short and lacks technical detail. "
                "An interviewer wants to see you explain the concepts clearly. "
                "Path parameters identify a specific resource, while query parameters filter or sort resources. "
                "Try to provide a more complete explanation next time."
            )
        else:
            # Good response
            score = 85
            feedback = (
                f"Excellent explanation! You scored {score}/100. "
                "You clearly described the difference: path parameters are used for resource identification and routing "
                "whereas query parameters are used for optional filtering, sorting, or pagination. "
                "This demonstrates solid understanding of RESTful API design."
            )
            
        return InterviewFeedback(
            question=question,
            user_answer=user_answer,
            feedback=feedback,
            score=score
        )
    else:
        # Question generation (fallback path — normally pre-empted by run_interview_agent)
        topic_match = re.search(r"topic:\s*(.*)", node_input, re.IGNORECASE)
        topic = (topic_match.group(1).strip() if topic_match else "General SWE").rstrip(". ,")
        return InterviewFeedback(
            question=_interview_question_fallback(topic),
            user_answer="", feedback="", score=0,
        )


@node(rerun_on_resume=True)
async def run_resume_agent(ctx: Context, node_input: str) -> GapReport:
    if os.environ.get("MOCK_LLM") == "True":
        return mock_resume_agent_node(node_input)
    res = await ctx.run_node(resume_agent, node_input=node_input)
    if isinstance(res, dict):
        return GapReport(**res)
    return res

@node(rerun_on_resume=True)
async def run_roadmap_agent(ctx: Context, node_input: str) -> LearningRoadmap:
    if os.environ.get("MOCK_LLM") == "True":
        return mock_roadmap_agent_node(node_input)
    res = await ctx.run_node(roadmap_agent, node_input=node_input)
    if isinstance(res, dict):
        return LearningRoadmap(**res)
    return res

async def run_interview_agent(ctx: Context, node_input: str) -> InterviewFeedback:
    is_eval = "Evaluate" in node_input or "User Answer:" in node_input

    if not is_eval:
        if os.environ.get("MOCK_LLM") == "True":
            _m = re.search(r"topic:\s*(.*)", node_input, re.IGNORECASE)
            _topic = (_m.group(1).strip() if _m else "General SWE").rstrip(". ,")
            return InterviewFeedback(
                question=_interview_question_fallback(_topic),
                user_answer="", feedback="", score=0,
            )

        # Question generation — MOCK_LLM=True short-circuits to the fallback question.
        # Otherwise, routes through the existing interview_agent LlmAgent with its own
        # hardcoded fallback on API failure or timeout.
        try:
            _key = os.environ.get("GOOGLE_API_KEY", "")
            _masked = (_key[:6] + "***" + _key[-4:]) if len(_key) > 10 else ("***" if _key else "<MISSING>")
            logger.warning(
                f"[interview] calling interview_agent | "
                f"GOOGLE_API_KEY={_masked} | "
                f"GOOGLE_GENAI_USE_VERTEXAI={os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '<unset>')}"
            )
            res = await asyncio.wait_for(
                ctx.run_node(interview_agent, node_input=node_input),
                timeout=10.0,
            )
            if isinstance(res, dict):
                return InterviewFeedback(**res)
            return res
        except (asyncio.TimeoutError, Exception) as _exc:
            logger.warning(
                f"[interview] question gen via interview_agent failed "
                f"({type(_exc).__name__}); using hardcoded fallback"
            )
            _m = re.search(r"topic:\s*(.*)", node_input, re.IGNORECASE)
            _topic = (_m.group(1).strip() if _m else "General SWE").rstrip(". ,")
            return InterviewFeedback(
                question=_interview_question_fallback(_topic),
                user_answer="", feedback="", score=0,
            )

    # Evaluation path — respect MOCK_LLM flag for mocked scoring
    if os.environ.get("MOCK_LLM") == "True":
        return await mock_interview_agent_node(node_input)
    res = await ctx.run_node(interview_agent, node_input=node_input)
    if isinstance(res, dict):
        return InterviewFeedback(**res)
    return res


# --- PII Scrubbing Helper ---

_EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
_PHONE_PATTERN = r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'

def scrub_pii(text: str) -> str:
    """Remove emails and phone numbers from text, replacing with redaction tokens."""
    text = re.sub(_EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
    text = re.sub(_PHONE_PATTERN, "[REDACTED_PHONE]", text)
    return text


# --- Workflow Nodes ---

def security_checkpoint(ctx: Context, node_input: Any) -> Event:
    user_text = ""
    if isinstance(node_input, str):
        user_text = node_input
    elif hasattr(node_input, "parts") and node_input.parts:
        parts_text = []
        for part in node_input.parts:
            if hasattr(part, "text") and part.text:
                parts_text.append(part.text)
            elif isinstance(part, str):
                parts_text.append(part)
        user_text = "".join(parts_text)
    elif hasattr(node_input, "text") and node_input.text:
        user_text = node_input.text
    elif isinstance(node_input, dict):
        user_text = node_input.get("text", str(node_input))
    else:
        user_text = str(node_input)

    # 1. PII Scrubbing (delegated to shared helper)
    scrubbed_text = scrub_pii(user_text)

    # 2. Prompt Injection Detection
    injection_keywords = [
        "ignore previous instructions", 
        "system prompt", 
        "override instructions", 
        "jailbreak", 
        "ignore rules",
        "do not scrub"
    ]
    
    is_injection = False
    for kw in injection_keywords:
        if kw in user_text.lower():
            is_injection = True
            break

    # 3. Domain-specific validation (check if input is relevant to SWE/career prep)
    # Check for general tech terms in JD or queries to ensure relevancy
    relevancy_flag = True
    tech_keywords = ["developer", "engineer", "software", "coder", "programmer", "tech", "code", "programming", "intern"]
    if len(user_text) > 100 and not any(kw in user_text.lower() for kw in tech_keywords):
        relevancy_flag = False

    audit_data = {
        "event": "security_check",
        "pii_detected": user_text != scrubbed_text,
        "injection_detected": is_injection,
        "domain_relevant": relevancy_flag,
        "severity": "CRITICAL" if is_injection else ("WARNING" if not relevancy_flag or user_text != scrubbed_text else "INFO")
    }
    
    # Write structured JSON log
    logger.warning(json.dumps(audit_data))

    if is_injection:
        return Event(output="Security Warning: Prompt injection detected. Execution blocked.", route="SECURITY_EVENT")

    return Event(output=scrubbed_text, route="PASS")

def security_error_node(node_input: str) -> Event:
    content = types.Content(role="model", parts=[types.Part.from_text(text=node_input)])
    return Event(content=content)

def orchestrator(ctx: Context, node_input: str) -> Event:
    user_msg = node_input.strip()
    user_msg_lower = user_msg.lower()

    # Route to active interview if topic is set
    if ctx.state.get("active_interview_topic"):
        return Event(output=user_msg, route="run_interview")

    if user_msg_lower.startswith(("/analyze", "/anlyze", "/analise", "/analysis", "/analyse")):
        parts = user_msg.split()
        resume_p = "data/resume.txt"
        jd_p = "data/sample_jd_wso2_backend_intern.txt"
        if len(parts) > 1:
            resume_p = parts[1]
        if len(parts) > 2:
            jd_p = parts[2]
            
        ctx.state["resume_path"] = resume_p
        ctx.state["jd_path"] = jd_p
        return Event(output=f"Analyzing resume {resume_p} and job description {jd_p}...", route="analyze_resume")

    elif user_msg_lower.startswith(("/roadmap", "/roadmape", "/road-map", "/road_map", "/road map")):
        return Event(output="Generating learning roadmap...", route="generate_roadmap")

    elif user_msg_lower.startswith(("/interview", "/intervew", "/interviewing", "/mock")):
        parts = user_msg.split()
        topic = "General SWE"
        if len(parts) > 1:
            raw_topic = " ".join(parts[1:])
            # Detect literal square brackets typed by the user (e.g. /interview [SQL])
            if "[" in raw_topic or "]" in raw_topic:
                cleaned = raw_topic.replace("[", "").replace("]", "").strip()
                hint = (
                    f"💡 Did you mean `/interview {cleaned}` (no brackets)?\n\n"
                    f"Square brackets `[ ]` are just placeholders in the help text — "
                    f"type the topic directly, e.g. `/interview {cleaned}`."
                )
                content = types.Content(role="model", parts=[types.Part.from_text(text=hint)])
                return Event(content=content, route="exit")
            topic = raw_topic
        # Handle nospace variant: /interview[SQL] → topic = "SQL"
        elif user_msg_lower.startswith(("/interview[", "/mock[")):
            bracket_start = user_msg.index("[")
            raw_topic = user_msg[bracket_start:].replace("[", "").replace("]", "").strip()
            cleaned = raw_topic or "the topic"
            hint = (
                f"💡 Did you mean `/interview {cleaned}` (no brackets)?\n\n"
                f"Square brackets `[ ]` are just placeholders — "
                f"type the topic directly, e.g. `/interview {cleaned}`."
            )
            content = types.Content(role="model", parts=[types.Part.from_text(text=hint)])
            return Event(content=content, route="exit")
        ctx.state["active_interview_topic"] = topic
        return Event(output=topic, route="run_interview")

    elif user_msg_lower.startswith(("/exit", "/quit", "/close")):
        msg = "Exiting session. Good luck with your placement prep!"
        content = types.Content(role="model", parts=[types.Part.from_text(text=msg)])
        return Event(content=content, route="exit")

    else:
        error_msg = (
            f"❌ Unrecognized command: `{user_msg}`\n\n"
            "Here are the available commands:\n\n"
            "1. `/analyze [resume_path] [jd_path]` — Parse resume and JD to identify skill gaps.\n"
            "   *(Default paths: data/resume.pdf data/sample_jd_wso2_backend_intern.txt)*\n"
            "2. `/roadmap` — Generate a personalized learning roadmap with concrete projects.\n"
            "3. `/interview <topic>` — Start a mock interview on a skill/topic (e.g. `/interview Java`).\n"
            "4. `/exit` — Exit the prep session.\n\n"
            "Please enter a valid command to begin."
        )
        content = types.Content(role="model", parts=[types.Part.from_text(text=error_msg)])
        return Event(content=content, route="exit")

def prepare_resume_input(ctx: Context) -> str:
    resume_path = ctx.state.get("resume_path", "data/resume.txt")
    jd_path = ctx.state.get("jd_path", "data/sample_jd_wso2_backend_intern.txt")
    
    from app.app_utils.document_reader import read_resume, read_job_description
    try:
        resume_text = read_resume(resume_path)
        jd_text = read_job_description(jd_path)
        # Scrub PII from file contents before sending to the LLM agent
        resume_text = scrub_pii(resume_text)
        jd_text = scrub_pii(jd_text)
        return f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}"
    except Exception as e:
        return f"ERROR: Failed to read files. Details: {e}"

def save_resume_result(ctx: Context, node_input: GapReport) -> Event:
    ctx.state["gap_report"] = node_input.model_dump()
    
    # Update progress in MCP server local store
    try:
        from app.mcp_server import update_progress
        update_progress({"gap_report": node_input.model_dump(), "current_status": "Resume Analyzed"})
    except Exception:
        pass
        
    response = (
        f"### Skill Gap Report\n\n"
        f"**Overall Fit Summary:** {node_input.summary}\n\n"
        f"**Missing Skills:** {', '.join(node_input.missing) if node_input.missing else 'None'}\n\n"
        f"**Weak Skills:**\n" + 
        "\n".join([f"{idx}. *{w.skill}*: {w.reason}" for idx, w in enumerate(node_input.weak, 1)]) + "\n\n"
        f"**Strong Skills:**\n" + 
        "\n".join([f"{idx}. *{s.skill}*: {s.evidence}" for idx, s in enumerate(node_input.strong, 1)]) + "\n\n"
        f"Type `/roadmap` to generate your learning roadmap."
    )
    content = types.Content(role="model", parts=[types.Part.from_text(text=response)])
    return Event(content=content)

def prepare_roadmap_input(ctx: Context) -> str:
    gap_report = ctx.state.get("gap_report")
    if not gap_report:
        return "ERROR: No gap report found in session state. Please run `/analyze` first."
        
    completed_skills = []
    try:
        from app.mcp_server import get_progress
        progress = get_progress()
        completed_skills = progress.get("completed_skills", [])
    except Exception:
        pass
        
    return f"GAP REPORT:\n{json.dumps(gap_report)}\n\nCOMPLETED SKILLS:\n{json.dumps(completed_skills)}"

def save_roadmap_result(ctx: Context, node_input: LearningRoadmap) -> Event:
    ctx.state["roadmap"] = node_input.model_dump()
    
    try:
        from app.mcp_server import update_progress
        update_progress({"learning_roadmap": node_input.model_dump(), "current_status": "Roadmap Generated"})
    except Exception:
        pass
        
    items_md = []
    for idx, item in enumerate(node_input.items, 1):
        link_str = f" ([Video Resource]({item.resource_link}))" if item.resource_link else ""
        items_md.append(
            f"{idx}. **{item.skill}** (Priority: {item.priority}){link_str}\n"
            f"   - *Resource*: {item.resource_or_method}\n"
            f"   - *Suggested Project*: {item.suggested_project}"
        )
        
    response = (
        f"### Personalized Learning Roadmap\n\n"
        f"{node_input.summary}\n\n"
        f"**Action Plan:**\n" + "\n".join(items_md) + "\n\n"
        f"Type `/interview <topic>` to start a mock interview on a skill (e.g. `/interview Python`)."
    )
    content = types.Content(role="model", parts=[types.Part.from_text(text=response)])
    return Event(content=content)

@node(rerun_on_resume=True)
async def run_interview_cycle(ctx: Context, node_input: str):
    # Read topic from snapshot first (set at question-generation time), falling
    # back to active_interview_topic, then default.  This ensures the evaluation
    # phase always logs the REAL skill even if active_interview_topic was reset.
    topic = (
        ctx.state.get("interview_topic_snapshot")
        or ctx.state.get("active_interview_topic")
        or "General SWE"
    )
    
    if ctx.state.get("interview_question") is None:
        prompt = f"Please generate a single challenging technical interview question for the topic: {topic}."
        feedback = await run_interview_agent(ctx, prompt)
        
        ctx.state["interview_question"] = feedback.question
        # Snapshot the topic so evaluation phase always has the real topic,
        # even if active_interview_topic is reset before this node resumes.
        ctx.state["interview_topic_snapshot"] = topic
        
        # Use a unique interrupt_id each time so the dialog always pops up fresh
        interview_count = ctx.state.get("interview_count", 0) + 1
        ctx.state["interview_count"] = interview_count
        interrupt_id = f"user_answer_{interview_count}"
        ctx.state["interview_interrupt_id"] = interrupt_id
        
        response = (
            f"### Mock Interview: {topic}\n\n"
            f"**Question:** {feedback.question}\n\n"
            f"Please reply with your answer."
        )
        content = types.Content(role="model", parts=[types.Part.from_text(text=response)])
        yield Event(content=content)
        yield RequestInput(interrupt_id=interrupt_id)
        return

    user_answer = None
    if ctx.resume_inputs:
        # Explicit is-not-None checks: an empty string is a valid answer and
        # must NOT be overwritten by the next fallback in the chain.
        interrupt_id = ctx.state.get("interview_interrupt_id", "user_answer")
        val = ctx.resume_inputs.get(interrupt_id)
        if val is None:
            val = ctx.resume_inputs.get("user_answer")
        if val is None:
            val = next(iter(ctx.resume_inputs.values()), None)
        if val is None:
            val = node_input
        user_answer = val if val is not None else "[No answer received]"
    else:
        user_answer = node_input if node_input is not None else "[No answer received]"

    

    # If the user types a command while in an interview, cancel the interview
    user_answer_str = str(user_answer).strip()
    if user_answer_str.startswith(("/", "\\")):
        ctx.state["interview_question"] = None
        ctx.state["active_interview_topic"] = None
        ctx.state["interview_topic_snapshot"] = None
        msg = f"Interview cancelled. Please type your command `{user_answer_str}` again to run it."
        content = types.Content(role="model", parts=[types.Part.from_text(text=msg)])
        yield Event(content=content)
        return

    active_q = ctx.state.get("interview_question", "Explain your understanding of this topic.")
    
    prompt = f"Topic: {topic}\nQuestion: {active_q}\nUser Answer: {user_answer}\nEvaluate and score this answer."
    feedback = await run_interview_agent(ctx, prompt)
    
    # Save results to session state
    history = ctx.state.get("interview_feedback", [])
    history.append(feedback.model_dump())
    ctx.state["interview_feedback"] = history
    
    # Save results to local progress store
    try:
        from app.mcp_server import get_progress, update_progress
        progress = get_progress()
        hist_list = progress.get("interview_history", [])
        # Include topic in the history entry so each record is self-contained
        history_entry = feedback.model_dump()
        history_entry["topic"] = topic
        hist_list.append(history_entry)
        
        completed = progress.get("completed_skills", [])
        if feedback.score >= 70 and topic.lower() not in [c.lower() for c in completed]:
            completed.append(topic)
            
        update_progress({
            "interview_history": hist_list,
            "completed_skills": completed
        })
    except Exception:
        pass
        
    # Reset interview state (snapshot cleared too)
    ctx.state["interview_question"] = None
    ctx.state["active_interview_topic"] = None
    ctx.state["interview_topic_snapshot"] = None
    
    evaluation_response = (
        f"### Mock Interview Evaluation\n\n"
        f"**Question:** {active_q}\n"
        f"**Your Answer:** {user_answer}\n\n"
        f"**Score:** {feedback.score}/100\n"
        f"**Feedback:** {feedback.feedback}\n\n"
        f"Type `/roadmap` to see your updated roadmap, or `/interview <topic>` to try again."
    )
    content = types.Content(role="model", parts=[types.Part.from_text(text=evaluation_response)])
    yield Event(content=content)

def handle_exit(node_input: Any) -> Any:
    return node_input

def handle_default(node_input: Any) -> Any:
    return node_input

from google.genai import types

def final_output(node_input: Any) -> Event:
    content = types.Content(
        role="model",
        parts=[types.Part.from_text(text=str(node_input))]
    )
    return Event(content=content, output=str(node_input))


# --- ADK 2.0 Workflow Definition ---

root_agent = Workflow(
    name="career_copilot_workflow",
    description="Career Copilot multi-agent resume matching, roadmap generation, and mock interview coaching workflow.",
    edges=[
        (START, security_checkpoint),
        
        (security_checkpoint, {
            "SECURITY_EVENT": security_error_node, 
            "PASS": orchestrator
        }),
        
        (orchestrator, {
            "analyze_resume": prepare_resume_input,
            "generate_roadmap": prepare_roadmap_input,
            "run_interview": run_interview_cycle,
            "exit": handle_exit,
            "__DEFAULT__": handle_default
        }),
        
        (prepare_resume_input, run_resume_agent),
        (run_resume_agent, save_resume_result),
        
        (prepare_roadmap_input, run_roadmap_agent),
        (run_roadmap_agent, save_roadmap_result),
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
