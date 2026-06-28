import json
import os
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from app.app_utils.document_reader import read_resume, read_job_description

# Initialize MCP server
mcp = FastMCP("career-copilot-mcp")

# Paths
BASE_DIR = Path(__file__).parent.parent
PROGRESS_FILE = BASE_DIR / "storage" / "progress.json"

@mcp.tool()
def read_resume_text(file_path: str) -> str:
    """Reads a resume file (PDF, DOCX, or TXT) and returns its plain text content.
    
    Args:
        file_path: The absolute or relative path to the resume file.
    """
    try:
        # Resolve path relative to BASE_DIR if it's relative
        path = Path(file_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        return read_resume(str(path))
    except Exception as e:
        print(f"Error reading resume {file_path}: {e}", file=sys.stderr)
        raise ValueError(f"Failed to read resume: {e}")

@mcp.tool()
def read_job_description_text(jd_path_or_text: str) -> str:
    """Reads a job description from a file path or returns the pasted text.
    
    Args:
        jd_path_or_text: Paste of JD text or a file path containing the job description.
    """
    try:
        path = Path(jd_path_or_text)
        if not path.is_absolute() and path.exists():
            path = BASE_DIR / path
            return read_job_description(str(path))
        return read_job_description(jd_path_or_text)
    except Exception as e:
        print(f"Error reading JD: {e}", file=sys.stderr)
        raise ValueError(f"Failed to read job description: {e}")

@mcp.tool()
def get_progress() -> dict:
    """Reads the candidate's learning progress and mock interview history from local storage.
    
    Returns:
        A dictionary containing progress tracking and interview logs.
    """
    try:
        if not PROGRESS_FILE.exists():
            return {"learning_roadmap": {}, "interview_history": [], "current_status": "Not Started"}
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading progress store: {e}", file=sys.stderr)
        return {"error": str(e)}

@mcp.tool()
def update_progress(progress_data: dict) -> str:
    """Saves updated learning progress, target goals, or mock interview scores back to local storage.
    
    Args:
        progress_data: A dictionary containing the updated fields to save.
    """
    try:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Merge with existing progress if exists
        current = {}
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    current = json.load(f)
            except Exception:
                pass
        
        current.update(progress_data)
        
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        return "Success: Progress store updated."
    except Exception as e:
        print(f"Error updating progress store: {e}", file=sys.stderr)
        raise ValueError(f"Failed to update progress store: {e}")

if __name__ == "__main__":
    mcp.run()
