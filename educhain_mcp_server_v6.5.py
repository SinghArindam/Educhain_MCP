import os
import json
from google import genai
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

def get_gemini_response(prompt: str) -> str:
    """
    Get a response from the Gemini API for a given prompt.
    
    Args:
        prompt (str): The input prompt to send to the Gemini API.
    
    Returns:
        str: The response text from the Gemini API.
    """
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return response.text


def clean_and_parse_json(json_string):
    """
    Cleans a string by removing common unnecessary characters and escape sequences,
    then attempts to parse it as JSON.

    Args:
        json_string: The string potentially containing JSON with extra characters.

    Returns:
        A Python dictionary/list if parsing is successful, None otherwise.
        Raises a ValueError if the cleaned string is still not valid JSON.
    """
    # Remove common problematic characters and escape sequences
    # This is a heuristic and might need adjustment based on specific input patterns.
    cleaned_string = json_string.replace("'''", " ") \
                                .replace('"""', " ") \
                                .replace('```', " ") \
                                .replace('`', " ") \
                                .replace('**', " ") \
                                .replace('*', " ") \
                                .replace('\\n', ' ') \
                                .replace('\\t', ' ') \
                                .replace('\\"', '"') \
                                .replace("\\'", "'")\
                                .replace('\n', ' ') \
                                .replace('\t', ' ') \
                                .replace('\"', '"') \
                                .replace("\'", "'")\
                                .replace('\\', ' ').strip()  # Remove leading/trailing whitespace

    # Attempt to parse the cleaned string as JSON
    try:
        return json.loads(cleaned_string)
    except json.JSONDecodeError as e:
        # If still not valid JSON, it's better to raise an error
        # or provide more specific feedback than just returning None silently.
        raise ValueError(f"Could not decode JSON after cleaning: {e}. Cleaned string: '{cleaned_string}'")

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
def generate_lesson_plan(topic: str, grade_level: str = "Middle School", duration: int = 60) -> Dict[str, Any]:
    """
    Generate a comprehensive lesson plan for the given topic using Gemini directly.
    """
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
        "learning_objectives": [
            "Objective 1",
            "Objective 2",
            "Objective 3"
        ],
        "materials_needed": [
            "Material 1",
            "Material 2",
            "Material 3"
        ],
        "lesson_structure": {{
            "introduction": {{
                "duration": "10 minutes",
                "activities": [
                    "Activity description"
                ]
            }},
            "main_content": {{
                "duration": "35 minutes",
                "activities": [
                    "Activity 1 description",
                    "Activity 2 description"
                ]
            }},
            "conclusion": {{
                "duration": "10 minutes",
                "activities": [
                    "Wrap-up activity"
                ]
            }},
            "assessment": {{
                "duration": "5 minutes",
                "activities": [
                    "Assessment method"
                ]
            }}
        }},
        "key_concepts": [
            "Concept 1",
            "Concept 2",
            "Concept 3"
        ],
        "homework_assignment": "Description of homework or follow-up activities",
        "additional_resources": [
            "Resource 1",
            "Resource 2"
        ]
    }}

    Make sure the response is valid JSON only, no additional text.
    """

    try:
        # Generate lesson plan using Gemini
        response = get_gemini_response(prompt)
        
        # Extract the content from the response
        content = response #.content if hasattr(response, 'content') else str(response)
        
        # Parse the JSON response
        lesson_plan = json.loads(content)
        
        # Validate that it's a dictionary
        if isinstance(lesson_plan, dict):
            return lesson_plan
        else:
            # Fallback if JSON parsing fails
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
                        "activities": [f"Detailed explanation of {topic}", f"Interactive {topic} activities"]
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
            
    except json.JSONDecodeError as e:
        # Return a structured fallback if JSON parsing fails
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
            "materials_needed": ["Whiteboard", "Presentation slides", "Student handouts"],
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
            "homework_assignment": f"Research and write about {topic} applications",
            "additional_resources": ["Textbook chapters", "Online videos", "Practice worksheets"],
            "error": f"JSON parsing failed: {str(e)}"
        }
    except Exception as e:
        # Return error information
        return {
            "title": f"Lesson Plan: {topic}",
            "topic": topic,
            "grade_level": grade_level,
            "duration": duration,
            "error": f"Failed to generate lesson plan: {str(e)}"
        }

@mcp.tool()
def generate_flashcards(topic: str, level: str = "Beginner", num: int = 5) -> list[dict]:
    mcqs = generate_mcqs(topic, level, num)
    return [{"question": q["question"], "answer": q["answer"]} for q in mcqs]

if __name__ == "__main__":
    mcp.run()