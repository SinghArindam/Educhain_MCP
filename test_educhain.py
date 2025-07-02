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

def generate_flashcards(topic: str,
                        level: str = "Beginner",
                        num: int = 5,
                        client=client) -> list[dict]:
    """
    Produce <num> Q-A flashcards for spaced repetition.
    """
    # Re-use Educhain’s MCQ generator, then strip choices so each card is Q + A
    mcqs = generate_mcqs(topic, level, num, client)
    print("MCQs generated:")
    print(mcqs)
    for q in mcqs:
        print(q)
        print(type(q))
        print(q.keys())
        print(type(q.keys()))
        print(q.values())
        print(type(q.values()))
    flashcards = [{"question": dict(q)["question"], "answer": dict(q)["answer"]}
                  for q in mcqs]
    return flashcards

# res = generate_mcqs("Python Programming", "Intermediate", 5)
# print(res)

# res2 = generate_lesson_plan("Python Programming", "Intermediate", "60 minutes", ["Understanding Python syntax", "Writing basic functions"])
# print(res2)

res3 = generate_flashcards("Python Programming", "Advanced", 5)
print(res3)

# formatted_content = """
# res = generate_mcqs("Python Programming", "Intermediate", 5)
# {res}


# res2 = generate_lesson_plan("Python Programming", "Intermediate", "60 minutes", ["Understanding Python syntax", "Writing basic functions"])
# {res2}


# res3 = generate_flashcards("Python Programming", "Advanced", 5)
# {res3}
# """

# # Write formatted version to another file
# with open('educhain_output_formatted.txt', 'a+') as file:
#     file.write(formatted_content)

# print("Formatted content successfully written to 'educhain_output_formatted.txt'")