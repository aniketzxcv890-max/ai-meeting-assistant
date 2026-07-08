import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()  # reads your .env file


# ---------------------------------------------------------------------------
# Data structure that holds all LLM analysis results
# ---------------------------------------------------------------------------
@dataclass
class AnalysisResult:
    summary: str
    action_items: list[dict]   # [{"task": ..., "assignee": ..., "deadline": ...}]
    key_decisions: list[str]   # ["Decision 1", "Decision 2", ...]
    model_used: str


# ---------------------------------------------------------------------------
# Helper to load prompt templates from the prompts/ folder
# ---------------------------------------------------------------------------
def load_prompt(filename: str, transcript: str) -> str:
    """Read a prompt template file and inject the transcript into it."""
    prompt_path = os.path.join("app", "prompts", filename)
    with open(prompt_path, "r") as f:
        template = f.read()
    return template.replace("{transcript}", transcript)


# ---------------------------------------------------------------------------
# Main analyzer class
# ---------------------------------------------------------------------------
class MeetingAnalyzer:
    """
    Sends the transcript to Gemini and returns structured analysis.

    Usage:
        analyzer = MeetingAnalyzer()
        result = analyzer.analyze("Full transcript text here...")
        print(result.summary)
        print(result.action_items)
        print(result.key_decisions)
    """

    MODEL_NAME = "gemini-2.5-flash"   # fast and free-tier friendly

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Make sure it is set in your .env file."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.MODEL_NAME)
        print(f"Analyzer ready — using model: {self.MODEL_NAME}")

    def _call_llm(self, prompt: str) -> str:
        """Send a prompt to Gemini and return the raw text response."""
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def _parse_json(self, raw: str, fallback: list) -> list:
        """
        Safely parse a JSON response from the LLM.
        If parsing fails, log the issue and return the fallback value
        so the app doesn't crash.
        """
        # Strip markdown code fences if the model added them
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse JSON from LLM response:\n{raw}")
            return fallback

    def get_summary(self, transcript: str) -> str:
        """Generate a concise meeting summary."""
        prompt = load_prompt("summary_prompt.txt", transcript)
        return self._call_llm(prompt)

    def get_action_items(self, transcript: str) -> list[dict]:
        """Extract action items as a list of dicts."""
        prompt = load_prompt("action_items_prompt.txt", transcript)
        raw = self._call_llm(prompt)
        return self._parse_json(raw, fallback=[])

    def get_key_decisions(self, transcript: str) -> list[str]:
        """Extract key decisions as a list of strings."""
        prompt = load_prompt("decisions_prompt.txt", transcript)
        raw = self._call_llm(prompt)
        return self._parse_json(raw, fallback=[])

    def analyze(self, transcript: str) -> AnalysisResult:
        """
        Run all three analyses on the transcript.
        Calls the LLM three times (one per task) for cleaner, focused outputs.
        """
        if not transcript or len(transcript.strip()) < 20:
            raise ValueError("Transcript is too short or empty to analyze.")

        print("Generating summary...")
        summary = self.get_summary(transcript)

        print("Extracting action items...")
        action_items = self.get_action_items(transcript)

        print("Extracting key decisions...")
        key_decisions = self.get_key_decisions(transcript)

        print("Analysis complete.")

        return AnalysisResult(
            summary=summary,
            action_items=action_items,
            key_decisions=key_decisions,
            model_used=self.MODEL_NAME,
        )