# 1) Import the MCP helper class and Educhain engines
from mcp.server.fastmcp import FastMCP  # FastMCP builds servers with almost no boilerplate
# from educhain import qna_engine, content_engine  # Educhain’s two main generators

# 2) Give your server a human-readable name (shows up inside Claude)
mcp = FastMCP("Educhain MCP Server")

# 3) ---------- TOOL #1 : Generate MCQs ----------
@mcp.tool()
def generate_mcqs(topic: str,
                  level: str = "Beginner",
                  num: int = 5) -> list[dict]:
    return {"questions":"answer_mcq"}

# 4) ---------- TOOL #2 : Lesson Plan Generator ----------
@mcp.tool()
def generate_lesson_plan(topic: str,
                         level: str = "Beginner") -> dict:
    """
    Build a structured lesson plan for <topic> at <level>.
    """
    # plan = content_engine.generate_lesson_plan(topic, level)
    return {"questions":"answer_mcq"}

# 5) ---------- (BONUS) TOOL #3 : Flashcard Generator ----------
@mcp.tool()
def generate_flashcards(topic: str,
                        level: str = "Beginner",
                        num: int = 10) -> list[dict]:
    """
    Produce <num> Q-A flashcards for spaced repetition.
    """
    # Re-use Educhain’s MCQ generator, then strip choices so each card is Q + A
    # mcqs = qna_engine.generate_mcq(topic, level, num=num)
    flashcards = {"question": "question", "answer": "correct_answer"}
    return flashcards

# 6) ---------- ENTRY POINT ----------
if __name__ == "__main__":
    # Running the file starts the MCP event loop on STDIO (Claude Desktop’s default)
    mcp.run()
