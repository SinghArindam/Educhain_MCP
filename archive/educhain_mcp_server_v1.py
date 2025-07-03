# 1) Import the MCP helper class and Educhain engines
from mcp.server.fastmcp import FastMCP  # FastMCP builds servers with almost no boilerplate
from educhain import qna_engine, content_engine  # Educhain’s two main generators

from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

# def get_mcq():
#     client = Educhain()

#     # Basic MCQ generation
#     mcq = client.qna_engine.generate_questions(
#         topic="Solar System",
#         num=3,
#         question_type="Multiple Choice"
#     )

#     # Advanced MCQ with custom parameters
#     advanced_mcq = client.qna_engine.generate_questions(
#         topic=topic,
#         num=num,
#         question_type="Multiple Choice",
#         difficulty_level=level,
#         custom_instructions="Include recent discoveries"
#     )

#     print(mcq.model_dump_json())  # View in JSON format , For Dictionary format use mcq.model_dump()

# Using Gemini
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY
)
gemini_config = LLMConfig(custom_model=gemini_model)
# gemini_client = Educhain(gemini_config)

# Using GPT-4
# gpt4_model = ChatOpenAI(
#     model_name="gpt-4.1",
#     openai_api_key=OPENAI_API_KEY
# )
# gpt4_config = LLMConfig(custom_model=gpt4_model)
# gpt4_client = Educhain(gpt4_config)

# 2) Give your server a human-readable name (shows up inside Claude)
mcp = FastMCP("Educhain MCP Server")

# 3) ---------- TOOL #1 : Generate MCQs ----------
@mcp.tool()
def generate_mcqs(topic: str,
                  level: str = "Beginner",
                  num: int = 5) -> list[dict]:
    """
    Create <num> multiple-choice questions for <topic> at the given difficulty <level>.
    Returns a list of question dictionaries that Claude can read.
    """
    # client = Educhain())
    # gemini_client = Educhain(gemini_config)
    client = Educhain(gemini_config)
    
    # Advanced MCQ with custom parameters
    advanced_mcq = client.qna_engine.generate_questions(
        topic=topic,
        num=num,
        question_type="Multiple Choice",
        difficulty_level=level,
        # custom_instructions="Include recent discoveries"
    )
    questions = advanced_mcq.model_dump()
    
    # 3a) Call Educhain to create the questions
    # questions = qna_engine.generate_mcq(topic, level, num=num)
    # 3b) FastMCP automatically serialises Python objects to JSON
    return questions

# 4) ---------- TOOL #2 : Lesson Plan Generator ----------
@mcp.tool()
def generate_lesson_plan(topic: str,
                         level: str = "Beginner") -> dict:
    """
    Build a structured lesson plan for <topic> at <level>.
    """
    plan = content_engine.generate_lesson_plan(topic, level)
    return plan

# 5) ---------- (BONUS) TOOL #3 : Flashcard Generator ----------
@mcp.tool()
def generate_flashcards(topic: str,
                        level: str = "Beginner",
                        num: int = 10) -> list[dict]:
    """
    Produce <num> Q-A flashcards for spaced repetition.
    """
    # Re-use Educhain’s MCQ generator, then strip choices so each card is Q + A
    mcqs = qna_engine.generate_mcq(topic, level, num=num)
    flashcards = [{"question": q["question"], "answer": q["correct_answer"]}
                  for q in mcqs]
    return flashcards

# 6) ---------- ENTRY POINT ----------
if __name__ == "__main__":
    # Running the file starts the MCP event loop on STDIO (Claude Desktop’s default)
    mcp.run()
