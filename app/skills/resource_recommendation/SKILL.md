---
name: resource_recommendation
description: Surfaces dynamic YouTube search learning resources for skill gaps.
---

# Agent Skill: Resource Recommendation

## Purpose
Dynamically surfaces a relevant learning resource for each identified skill gap.

## Trigger
Invoked by `learning_roadmap_agent` once per skill gap during the `/roadmap` command.

## Input
- **skill**: Skill name (string, e.g., `"FastAPI"`)

## Output
- **resource_link**: YouTube search results URL (string, e.g., `"https://www.youtube.com/results?search_query=FastAPI+tutorial+for+beginners"`)

## Design Note
Deliberately uses a live search URL rather than a hardcoded/curated video link, to avoid stale or hallucinated links and guarantee the result always resolves to real, current content.
