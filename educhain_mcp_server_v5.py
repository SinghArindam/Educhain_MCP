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
def generate_lesson_plan(topic: str, grade_level: str, duration: int) -> Dict[str, Any]:
    """
    Generates a lesson plan for a given topic, grade level, and duration using EduChain.
    
    Args:
        topic (str): The subject or topic of the lesson (e.g., "Photosynthesis").
        grade_level (str): The target grade level (e.g., "Grade 5").
        duration (int): Duration of the lesson in minutes (e.g., 60).
    
    Returns:
        Dict[str, Any]: A structured lesson plan with objectives, activities, and assessments.
    """
    try:
        # Call EduChain's lesson plan generator
        lesson_plan = client.content_engine.generate_lesson_plan(
            topic=topic,
            grade_level=grade_level,
            duration=duration
        )
        return {
            "status": "success",
            "lesson_plan": {
                "topic": topic,
                "grade_level": grade_level,
                "duration": duration,
                "objectives": lesson_plan["objectives"],
                "activities": lesson_plan["activities"],
                "assessments": lesson_plan["assessments"]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate lesson plan: {str(e)}"
        }
    
@mcp.tool()
def generate_flashcards(topic: str, level: str = "Beginner", num: int = 5) -> list[dict]:
    mcqs = generate_mcqs(topic, level, num)
    return [{"question": q["question"], "answer": q["answer"]} for q in mcqs]

if __name__ == "__main__":
    mcp.run()