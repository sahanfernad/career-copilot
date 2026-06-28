import sys
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import google.auth
from unittest.mock import MagicMock
google.auth.default = MagicMock(return_value=(MagicMock(), "dummy-project"))

from app.agent import root_agent

session_service = InMemorySessionService()
session = session_service.create_session_sync(user_id="test_user", app_name="test")
runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

message = types.Content(
    role="user", parts=[types.Part.from_text(text="Why is the sky blue?")]
)

events = list(
    runner.run(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    )
)

print(f"Number of events: {len(events)}")
for i, event in enumerate(events):
    print(f"Event {i}: type={type(event)}")
    print(f"  content={repr(event.content)}")
    print(f"  output={repr(event.output)}")
    print(f"  message={repr(event.message)}")

