import os
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Initialize Educhain client with Gemini
client = Educhain(
    LLMConfig(
        custom_model=ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY")
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
def generate_lesson_plan(
    topic: str,
    grade_level: str = "Beginner",
    duration: str = "60 minutes",
    learning_objectives: list = ["Understanding the process", "Identifying key components"],
) -> dict:
    """
    Build a structured lesson plan for <topic> at <level>.
    """
    return json.loads(
        client.content_engine.generate_lesson_plan(
            topic=topic,
            duration=duration,
            grade_level=grade_level,
            learning_objectives=learning_objectives,
        ).model_dump_json()
    )

if __name__ == "__main__":
    mcp.run()