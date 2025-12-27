"""
OpenAI-based event filtering and summarization.

Uses OpenAI gpt-4o-mini for:
1. Filtering events by child relevance
2. Summarizing weekly events with recurring event consolidation
"""

import json
import re
from typing import List, Dict, Any
from openai import OpenAI


class OpenAISummarizer:
    """
    Filter and summarize calendar events using OpenAI API.
    """

    def __init__(self, api_key: str):
        """
        Initialize OpenAISummarizer.

        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def filter_and_summarize(
        self,
        events: List[Dict[str, Any]],
        children: List[Dict[str, Any]],
        week_start: str,
        week_end: str,
    ) -> Dict[str, Any]:
        """
        Filter events by child relevance and create a weekly summary.

        Args:
            events: List of calendar events for the week
            children: List of child profiles with their organisations
            week_start: ISO date string for week start (Monday)
            week_end: ISO date string for week end (Sunday)

        Returns:
            Dictionary with:
              - relevant_events: List of events relevant to children
              - summary: Text summary of the week
              - recurring_events: Grouped recurring events
              - highlights: Unique/notable events for the week
        """
        # Build prompt
        prompt = self._build_prompt(events, children, week_start, week_end)

        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that analyzes school calendar events "
                        "for parents. Return responses in valid JSON format."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2048,
            temperature=0.3,
        )

        # Parse response
        response_text = response.choices[0].message.content or ""

        # Try to parse JSON from response
        result: Dict[str, Any]
        try:
            json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if parsing fails
            result = {
                "raw_response": response_text,
                "relevant_events": [],
                "summary": "Unable to generate summary",
                "recurring_events": [],
                "highlights": [],
            }

        return result

    def _build_prompt(
        self,
        events: List[Dict[str, Any]],
        children: List[Dict[str, Any]],
        week_start: str,
        week_end: str,
    ) -> str:
        """Build the prompt for OpenAI."""

        children_info = []
        for child in children:
            child_info = {
                "name": child.get("name"),
                "year_level": child.get("year_level"),
                "interests": child.get("interests"),
                "organisations": [org.get("name") for org in child.get("organisations", [])],
            }
            children_info.append(child_info)

        return f"""
Analyze the following school calendar events for a parent with children.

## Week Period
From: {week_start} (Monday)
To: {week_end} (Sunday)

## Children Profiles
{json.dumps(children_info, indent=2)}

## Calendar Events
{json.dumps(events, indent=2, default=str)}

## Tasks
1. Filter events to only those RELEVANT to the children (based on their year level, organisations, and interests)
2. Identify RECURRING events (e.g., regular classes, weekly activities) and group them
3. Identify UNIQUE/NOTABLE events (excursions, special days, performances, etc.)
4. Write a brief SUMMARY paragraph highlighting what's happening this week

## Response Format
Return a JSON object with this structure:
```json
{{
  "relevant_events": [
    {{
      "id": "event_id",
      "title": "event title",
      "start": "ISO datetime",
      "end": "ISO datetime",
      "relevance_reason": "why this is relevant to the child",
      "child_name": "which child this relates to"
    }}
  ],
  "recurring_events": [
    {{
      "pattern": "description of recurring pattern (e.g., 'Daily 9am Assembly')",
      "event_ids": ["id1", "id2"],
      "count": 5
    }}
  ],
  "highlights": [
    {{
      "id": "event_id",
      "title": "event title",
      "why_notable": "reason this is a highlight",
      "action_needed": "any parent action required (or null)"
    }}
  ],
  "summary": "A brief 2-3 sentence summary of the week's activities for the children."
}}
```
"""
