# 1) Import the MCP helper class and Educhain engines
from mcp.server.fastmcp import FastMCP  # FastMCP builds servers with almost no boilerplate
import os
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")

# Using Gemini
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY
)
gemini_config = LLMConfig(custom_model=gemini_model)
client = Educhain(gemini_config)

# 2) Give your server a human-readable name (shows up inside Claude)
mcp = FastMCP("Educhain MCP Server")

# 3) ---------- TOOL #1 : Generate MCQs ----------
@mcp.tool()
def generate_mcqs(topic: str,
                  level: str = "Beginner",
                  num: int = 5,
                  client=client) -> list[dict]:
    """
    Create <num> multiple-choice questions for <topic> at the given difficulty <level>.
    Returns a list of question dictionaries that Claude can read.
    """
    
    advanced_mcq = client.qna_engine.generate_questions(
        topic=topic,
        num=num,
        question_type="Multiple Choice",
        difficulty_level=level,
    )
    questions = advanced_mcq.model_dump()
    return questions

# 4) ---------- TOOL #2 : Lesson Plan Generator ----------
@mcp.tool()
def generate_lesson_plan(topic: str,
                         grade_level: str = "Beginner",
                         duration: str = "60 minutes",
                         learning_objectives = ["Understanding the process", "Identifying key components"],
                         client=client) -> dict:
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
    plan = detailed_lesson.model_dump()
    return plan

# 5) ---------- (BONUS) TOOL #3 : Flashcard Generator ----------
# @mcp.tool()
# def generate_flashcards(topic: str,
#                         level: str = "Beginner",
#                         num: int = 5,
#                         client=client) -> list[dict]:
#     """
#     Produce <num> Q-A flashcards for spaced repetition.
#     """
#     # Re-use Educhain’s MCQ generator, then strip choices so each card is Q + A
#     mcqs = generate_mcqs(topic, level, num, client)
#     flashcards = [{"question": q["question"], "answer": q["correct_answer"]}
#                   for q in mcqs]
#     return flashcards

# 6) ---------- ENTRY POINT ----------
if __name__ == "__main__":
    # Running the file starts the MCP event loop on STDIO (Claude Desktop’s default)
    mcp.run()
