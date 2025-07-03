"""
===============================================================================
 Educhain MCP Server
===============================================================================

A lightweight **FastMCP** server that exposes three pedagogical tools backed by
Educhain’s Q&A engine and Google’s Gemini 2.5-flash LLM:

1. generate_mcqs     – Create multiple-choice questions for a topic.
2. generate_lesson_plan – Build a structured JSON lesson plan via Gemini.
3. generate_flashcards   – Convert MCQs into simple Q&A flashcards.

All functions are decorated with `@mcp.tool()` so they can be invoked over
HTTP / WebSocket by any MCP-compatible agent (e.g. Claude, ChatGPT).

Usage
-----
$ export GEMINI_API_KEY=<your-key>
$ python this_file.py
# FastMCP will start and print its listening URL.

Design Notes
------------
* Educhain is configured to use Gemini as its custom model via
  `langchain_google_genai.ChatGoogleGenerativeAI`.
* Gemini is also accessed **directly** for free-form generation in
  `generate_lesson_plan` through the lower-level `google.genai` client.
* The helper `clean_and_parse_json` can be reused if Gemini returns
  non-strict JSON (though it is not currently called in this script).

Author:  <your name / organisation>
"""

import os
import json
from google import genai
from typing import Dict, Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI

# ─────────────────────────────────────────────────────────────────────────────
# Environment & client setup
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()  # Reads GEMINI_API_KEY from .env or environment variables

# Initialize an Educhain client that internally uses Gemini 2.5-flash
client = Educhain(
    LLMConfig(
        custom_model=ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# Gemini helper wrappers
# ─────────────────────────────────────────────────────────────────────────────

def get_gemini_response(prompt: str) -> str:
    """
    Send a prompt to Google Gemini 2.5-flash and return the raw text response.

    Parameters
    ----------
    prompt : str
        Plain-text prompt sent to the model.

    Returns
    -------
    str
        The model’s textual response (`response.text`).
    """
    client = genai.Client()  # lightweight instantiation
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def clean_and_parse_json(json_string: str) -> Any:
    """
    Heuristically strip markdown fences / escape sequences and parse JSON.

    This helper is useful when an LLM encloses its JSON in triple-backticks or
    inserts stray escape characters that break `json.loads`.

    Parameters
    ----------
    json_string : str
        The raw string that *should* represent a JSON document.

    Returns
    -------
    Any
        A Python dict / list if parsing succeeds.

    Raises
    ------
    ValueError
        If the cleaned string still cannot be decoded as JSON.
    """
    # Remove common problematic characters and escape sequences
    # Note: this list can be extended as new artefacts are observed.
    cleaned_string = (
        json_string.replace("'''", " ")
        .replace('"""', " ")
        .replace('```
        .replace('`', " ")
        .replace('**', " ")
        .replace('*', " ")
        .replace('\\n', ' ')
        .replace('\\t', ' ')
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace('\n', ' ')
        .replace('\t', ' ')
        .replace('\"', '"')
        .replace("\'", "'")
        .replace('\\', ' ')
        .strip()                               # remove leading/trailing space
    )

    try:
        return json.loads(cleaned_string)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Could not decode JSON after cleaning: {e}. "
            f"Cleaned string: '{cleaned_string}'"
        )

# ─────────────────────────────────────────────────────────────────────────────
# FastMCP server and tool definitions
# ─────────────────────────────────────────────────────────────────────────────

mcp = FastMCP("Educhain MCP Server")  # Human-readable server name

@mcp.tool()
def generate_mcqs(topic: str, level: str = "Beginner", num: int = 5) -> list[dict]:
    """
    Generate `num` multiple-choice questions for a given topic and difficulty.

    Parameters
    ----------
    topic : str
        Subject area, e.g. "Photosynthesis".
    level : str, default "Beginner"
        Difficulty label understood by Educhain ("Beginner", "Intermediate", ...).
    num : int, default 5
        Number of MCQs requested.

    Returns
    -------
    list[dict]
        A list of Educhain question dictionaries.  Each dictionary typically
        contains: `question`, `options`, `answer`, `explanation`, ...
    """
    return (
        client.qna_engine.generate_questions(
            topic=topic,
            num=num,
            question_type="Multiple Choice",
            difficulty_level=level
        )
        .model_dump()
        ["questions"]
    )

@mcp.tool()
def generate_lesson_plan(
    topic: str,
    grade_level: str = "Middle School",
    duration: int = 60
) -> Dict[str, Any]:
    """
    Build a fully-fledged lesson plan in JSON form via Gemini.

    Gemini is instructed *explicitly* to output raw JSON (no markdown).
    The function attempts to `json.loads` the response and, if that fails,
    returns a deterministic fallback dictionary so that the caller never
    receives invalid JSON.

    Parameters
    ----------
    topic : str
        Lesson subject.
    grade_level : str, default "Middle School"
        Intended grade level.
    duration : int, default 60
        Lesson duration in minutes.

    Returns
    -------
    dict
        A structured lesson-plan object (see prompt for schema).  If any error
        occurs, the dictionary contains an `"error"` key describing the issue.
    """
    # ---------- Prompt engineering block ------------------------------------
    prompt = f"""
    Create a detailed lesson plan for the topic: "{topic}"
    Grade Level: {grade_level}
    Duration: {duration} minutes

    Please provide the lesson plan in the following JSON format:
    {{
        "title": "Lesson title",
        "topic": "{topic}",
        "grade_level": "{grade_level}",
        "duration": "{duration}",
        "learning_objectives": [...],
        ...
    }}

    Make sure the response is valid JSON only, no additional text.
    """

    try:
        # Call Gemini
        response = get_gemini_response(prompt)

        # Gemini returns pure JSON (as requested).  No markdown fences expected.
        lesson_plan = json.loads(response)

        # Ensure the root is a dict (Gemini might sometimes return a list).
        if isinstance(lesson_plan, dict):
            return lesson_plan

        # ---------- Fallback when JSON root is not a dict -------------------
        return {
            "title": f"Lesson Plan: {topic}",
            "topic": topic,
            "grade_level": grade_level,
            "duration": duration,
            "learning_objectives": [
                f"Understand the basics of {topic}",
                f"Apply knowledge of {topic} in practical scenarios",
                f"Analyze and evaluate {topic} concepts"
            ],
            "materials_needed": ["Whiteboard", "Textbook", "Handouts"],
            "lesson_structure": {
                "introduction": {
                    "duration": "10 minutes",
                    "activities": [f"Introduction to {topic}"]
                },
                "main_content": {
                    "duration": "35 minutes",
                    "activities": [
                        f"Detailed explanation of {topic}",
                        f"Interactive {topic} activities"
                    ]
                },
                "conclusion": {
                    "duration": "10 minutes",
                    "activities": ["Summary and review"]
                },
                "assessment": {
                    "duration": "5 minutes",
                    "activities": ["Quick quiz or discussion"]
                }
            },
            "key_concepts": [f"Key concepts related to {topic}"],
            "homework_assignment": f"Complete exercises related to {topic}",
            "additional_resources": ["Online resources", "Recommended readings"],
            "error": "Generated with fallback structure"
        }

    # ---------- JSON parsing failed outright -------------------------------
    except json.JSONDecodeError as e:
        return {
            "title": f"Lesson Plan: {topic}",
            "topic": topic,
            "grade_level": grade_level,
            "duration": duration,
            "learning_objectives": [
                f"Understand the fundamentals of {topic}",
                f"Apply {topic} concepts in real-world scenarios",
                f"Evaluate and analyze {topic} information"
            ],
            "materials_needed": [
                "Whiteboard", "Presentation slides", "Student handouts"
            ],
            "lesson_structure": {
                "introduction": {
                    "duration": "10 minutes",
                    "activities": [f"Warm-up activity introducing {topic}"]
                },
                "main_content": {
                    "duration": "35 minutes",
                    "activities": [
                        f"Lecture on {topic} fundamentals",
                        f"Interactive {topic} demonstration",
                        f"Group activity exploring {topic}"
                    ]
                },
                "conclusion": {
                    "duration": "10 minutes",
                    "activities": ["Review key points", "Q&A session"]
                },
                "assessment": {
                    "duration": "5 minutes",
                    "activities": ["Exit ticket or quick assessment"]
                }
            },
            "key_concepts": [f"Core principles of {topic}"],
            "homework_assignment": (
                f"Research and write about {topic} applications"
            ),
            "additional_resources": [
                "Textbook chapters", "Online videos", "Practice worksheets"
            ],
            "error": f"JSON parsing failed: {str(e)}"
        }

    # ---------- Any other unexpected exception -----------------------------
    except Exception as e:
        return {
            "title": f"Lesson Plan: {topic}",
            "topic": topic,
            "grade_level": grade_level,
            "duration": duration,
            "error": f"Failed to generate lesson plan: {str(e)}"
        }

@mcp.tool()
def generate_flashcards(
    topic: str,
    level: str = "Beginner",
    num: int = 5
) -> list[dict]:
    """
    Convert freshly generated MCQs into simple front/back flashcards.

    Parameters
    ----------
    topic : str
        Subject for which flashcards are produced.
    level : str, default "Beginner"
        Difficulty of the underlying MCQs.
    num : int, default 5
        Number of flashcards.

    Returns
    -------
    list[dict]
        Each element has two keys: `question` and `answer`.
    """
    mcqs = generate_mcqs(topic, level, num)
    return [
        {"question": q["question"], "answer": q["answer"]}
        for q in mcqs
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Starts the FastMCP HTTP / WS server.  The decorated functions above are
    # automatically exposed under their given names.
    mcp.run()
