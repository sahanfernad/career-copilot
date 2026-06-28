# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


def test_agent_stream() -> None:
    """
    Integration test for the agent stream functionality.
    Tests that the agent returns valid streaming responses.
    """

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
    assert len(events) > 0, "Expected at least one message"

    has_text_content = False
    for event in events:
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            break
    assert has_text_content, "Expected at least one message with text content"


def test_multiple_interviews() -> None:
    """
    Integration test to ensure that starting a second mock interview
    and answering it works correctly without raising KeyError.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # 1. Start first interview: /interview SQL
    msg1 = types.Content(role="user", parts=[types.Part.from_text(text="/interview SQL")])
    events1 = list(
        runner.run(
            new_message=msg1,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events1) > 0, "Expected events from starting the first interview"

    # 2. Answer first interview: no idea
    msg2 = types.Content(role="user", parts=[types.Part.from_text(text="no idea")])
    events2 = list(
        runner.run(
            new_message=msg2,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events2) > 0, "Expected events from evaluating the first interview"

    # 3. Start second interview: /interview Python
    msg3 = types.Content(role="user", parts=[types.Part.from_text(text="/interview Python")])
    events3 = list(
        runner.run(
            new_message=msg3,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events3) > 0, "Expected events from starting the second interview"

    # 4. Answer second interview: python is cool
    msg4 = types.Content(role="user", parts=[types.Part.from_text(text="python is cool")])
    events4 = list(
        runner.run(
            new_message=msg4,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events4) > 0, "Expected events from evaluating the second interview"

