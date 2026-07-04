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
Unit tests for the get_learning_resource_link MCP tool.
"""

from app.mcp_server import get_learning_resource_link


def test_resource_link_simple() -> None:
    """Test get_learning_resource_link with a simple skill name."""
    url = get_learning_resource_link("FastAPI")
    assert url == "https://www.youtube.com/results?search_query=FastAPI+tutorial+for+beginners"


def test_resource_link_with_spaces() -> None:
    """Test get_learning_resource_link with skill names containing spaces."""
    url = get_learning_resource_link("REST APIs")
    assert url == "https://www.youtube.com/results?search_query=REST+APIs+tutorial+for+beginners"


def test_resource_link_with_special_characters() -> None:
    """Test get_learning_resource_link with skill names containing special characters."""
    # Test React.js
    url_react = get_learning_resource_link("React.js")
    assert url_react == "https://www.youtube.com/results?search_query=React.js+tutorial+for+beginners"

    # Test CI/CD
    url_cicd = get_learning_resource_link("CI/CD")
    assert url_cicd == "https://www.youtube.com/results?search_query=CI%2FCD+tutorial+for+beginners"

    # Test C++
    url_cpp = get_learning_resource_link("C++")
    assert url_cpp == "https://www.youtube.com/results?search_query=C%2B%2B+tutorial+for+beginners"
