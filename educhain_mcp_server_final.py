import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize Educhain client with Gemini
client = Educhain(
    LLMConfig(
        custom_model=ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY")
        )
    )
)

mcp = FastMCP("Educhain MCP Server")

@mcp.tool()
def generate_mcqs(topic: str, level: str = "Beginner", num: int = 5) -> list[dict]:
    """
    Create <num> multiple-choice questions for <topic> at the given difficulty <level>.
    Returns a list of question dictionaries that Claude can read.
    """
    return client.qna_engine.generate_questions(
        topic=topic, num=num, question_type="Multiple Choice", difficulty_level=level
    ).model_dump()["questions"]

@mcp.tool()
def generate_lesson_plan(topic: str,
                         grade_level: str = "Beginner",
                         duration: int = 60,
                         learning_objectives = ["Understanding the process", "Identifying key components"]) -> dict:
    """
    Build a structured lesson plan for <topic> at <level>.
    """
    # Advanced lesson plan with specific parameters
    detailed_lesson = client.content_engine.generate_lesson_plan(
        topic=topic,
        duration=duration,
        grade_level=grade_level,
        learning_objectives=learning_objectives
    )
    plan = detailed_lesson.model_dump_json()
    # plan_json = json.loads(plan)  # Convert JSON string to Python dict
    # print(type(plan_json))
    return plan #plan_json

@mcp.tool()
def generate_flashcards(topic: str, level: str = "Beginner", num: int = 5) -> list[dict]:
    mcqs = generate_mcqs(topic, level, num)
    return [{"question": q["question"], "answer": q["answer"]} for q in mcqs]

if __name__ == "__main__":
    mcp.run()