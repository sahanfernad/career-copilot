"""
Part 1 — Orchestrator (skeleton)
----------------------------------
The orchestrator's job, per the blueprint, is to:
  1. Hold session state across all 3 agents (resume text, JD text,
     gap report, roadmap, interview results)
  2. Decide which agent runs next and what data flows between them

In Part 1, only Agent 1 exists, so this is intentionally thin — just the
shared state container and the one call we can make today. In Part 2,
once Agent 2 (Roadmap) exists, this will grow real routing logic: e.g.
"if gap_report exists and roadmap doesn't, run Agent 2 next."

We are NOT yet wiring this to ADK's Runner/SessionService internals —
that's worth doing properly once there's more than one agent to route
between, so we pull the exact current syntax from the ADK docs at that
point rather than guessing it now.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

PROGRESS_STORE_PATH = Path(__file__).parent / "storage" / "progress.json"


@dataclass
class SessionState:
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    gap_report: Optional[dict] = None      # filled by Agent 1
    roadmap: Optional[dict] = None         # filled by Agent 2 (Part 2)
    interview_history: list = field(default_factory=list)  # filled by Agent 3 (Part 3)

    def save_gap_report(self, gap_report: dict) -> None:
        self.gap_report = gap_report

    def to_dict(self) -> dict:
        return asdict(self)


def load_progress_store() -> dict:
    """Reads the local JSON progress file. Returns {} if it doesn't exist yet."""
    if not PROGRESS_STORE_PATH.exists():
        return {}
    return json.loads(PROGRESS_STORE_PATH.read_text(encoding="utf-8"))


def save_progress_store(data: dict) -> None:
    PROGRESS_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_STORE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # Smoke test: confirm the state container and store round-trip cleanly
    session = SessionState()
    session.resume_text = "sample resume text"
    session.jd_text = "sample JD text"
    print("SessionState created OK:")
    print(json.dumps(session.to_dict(), indent=2)[:300])
