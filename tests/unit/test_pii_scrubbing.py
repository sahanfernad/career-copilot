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
"""
Unit tests for the PII scrubbing functionality in Career Copilot.
"""

from app.agent import scrub_pii


def test_scrub_pii_email() -> None:
    """Test that email addresses are properly redacted."""
    input_text = "Please reach out to me at test@example.com for further inquiries."
    result = scrub_pii(input_text)
    assert "[REDACTED_EMAIL]" in result
    assert "test@example.com" not in result


def test_scrub_pii_phone() -> None:
    """Test that phone numbers are properly redacted."""
    input_text = "My phone number is 555-123-4567, feel free to call."
    result = scrub_pii(input_text)
    assert "[REDACTED_PHONE]" in result
    assert "555-123-4567" not in result


def test_scrub_pii_no_pii() -> None:
    """Test that text without PII remains completely unchanged."""
    input_text = "FastAPI is a modern web framework for building REST APIs."
    result = scrub_pii(input_text)
    assert result == input_text


def test_scrub_pii_combined() -> None:
    """Test that both email and phone numbers are redacted in a combined case."""
    input_text = "Contact info: user@domain.com or call +1 555-123-4567."
    result = scrub_pii(input_text)
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_PHONE]" in result
    assert "user@domain.com" not in result
    assert "555-123-4567" not in result
