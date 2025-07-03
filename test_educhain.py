import os
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from google import genai

from pprint import pprint
import json

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
    return questions["questions"]

def generate_lesson_plan(topic: str,
                         duration: int = 60,
                         grade_level: str = "Beginner",
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
    
    plan_cleaned = clean_and_parse_json(plan)
    pprint(plan_cleaned)  # Print the cleaned JSON object for debugging
    print(type(plan_cleaned))  # Should be a dict or list
    with open("lesson_plan.json", "w") as f:
        json.dump(plan_cleaned, f, indent=4)
    # content = f"""
    # Convert the given string into a valid JSON object, ensuring no unnecessary escape characters or extraneous backticks (`) or triple quotes or other inconsistencies remain.
    
    # {plan}
    
    # Return valid JSON object only.    
    # """
    # plan_formatted = get_gemini_response(content)
    # pprint(plan_formatted)
    # print(type(plan_formatted))  # Should be a string
    # plan_json = json.loads(plan_formatted)  # Convert JSON string to Python dict
    # print(type(plan_json))
    return plan_cleaned

# def generate_lesson_plan(topic: str,
#                          grade_level: str = "Beginner",
#                          duration: str = "60 minutes",
#                          learning_objectives = ["Understanding the process", "Identifying key components"],
#                          client=client) -> dict:
#     """
#     Build a structured lesson plan for <topic> at <level>.
#     """
#     # Advanced lesson plan with specific parameters
#     detailed_lesson = client.content_engine.generate_lesson_plan(
#         topic=topic,
#         duration=duration,
#         grade_level=grade_level,
#         learning_objectives=learning_objectives
#     )
#     plan = detailed_lesson.model_dump_json()
#     pprint(plan)  # Print the raw JSON string for debugging
#     print(type(plan))  # Should be a string
#     plan_json = json.loads(plan)  # Convert JSON string to Python dict
#     print(type(plan_json))
#     return plan_json

# def generate_lesson_plan(topic: str, grade_level: str = "Middle School", duration: str = "60 minutes") -> Dict[str, Any]:
#     """
#     Generate a comprehensive lesson plan for the given topic using Gemini directly.
#     """
#     prompt = f"""
#     Create a detailed lesson plan for the topic: "{topic}"
#     Grade Level: {grade_level}
#     Duration: {duration}

#     Please provide the lesson plan in the following JSON format:
#     {{
#         "title": "Lesson title",
#         "topic": "{topic}",
#         "grade_level": "{grade_level}",
#         "duration": "{duration}",
#         "learning_objectives": [
#             "Objective 1",
#             "Objective 2",
#             "Objective 3"
#         ],
#         "materials_needed": [
#             "Material 1",
#             "Material 2",
#             "Material 3"
#         ],
#         "lesson_structure": {{
#             "introduction": {{
#                 "duration": "10 minutes",
#                 "activities": [
#                     "Activity description"
#                 ]
#             }},
#             "main_content": {{
#                 "duration": "35 minutes",
#                 "activities": [
#                     "Activity 1 description",
#                     "Activity 2 description"
#                 ]
#             }},
#             "conclusion": {{
#                 "duration": "10 minutes",
#                 "activities": [
#                     "Wrap-up activity"
#                 ]
#             }},
#             "assessment": {{
#                 "duration": "5 minutes",
#                 "activities": [
#                     "Assessment method"
#                 ]
#             }}
#         }},
#         "key_concepts": [
#             "Concept 1",
#             "Concept 2",
#             "Concept 3"
#         ],
#         "homework_assignment": "Description of homework or follow-up activities",
#         "additional_resources": [
#             "Resource 1",
#             "Resource 2"
#         ]
#     }}

#     Make sure the response is valid JSON only, no additional text.
#     """

#     try:
#         # Generate lesson plan using Gemini
#         response = gemini_model.invoke(prompt)
        
#         # Extract the content from the response
#         content = response.content if hasattr(response, 'content') else str(response)
        
#         # Parse the JSON response
#         lesson_plan = json.loads(content)
        
#         # Validate that it's a dictionary
#         if isinstance(lesson_plan, dict):
#             return lesson_plan
#         else:
#             # Fallback if JSON parsing fails
#             return {
#                 "title": f"Lesson Plan: {topic}",
#                 "topic": topic,
#                 "grade_level": grade_level,
#                 "duration": duration,
#                 "learning_objectives": [
#                     f"Understand the basics of {topic}",
#                     f"Apply knowledge of {topic} in practical scenarios",
#                     f"Analyze and evaluate {topic} concepts"
#                 ],
#                 "materials_needed": ["Whiteboard", "Textbook", "Handouts"],
#                 "lesson_structure": {
#                     "introduction": {
#                         "duration": "10 minutes",
#                         "activities": [f"Introduction to {topic}"]
#                     },
#                     "main_content": {
#                         "duration": "35 minutes",
#                         "activities": [f"Detailed explanation of {topic}", f"Interactive {topic} activities"]
#                     },
#                     "conclusion": {
#                         "duration": "10 minutes",
#                         "activities": ["Summary and review"]
#                     },
#                     "assessment": {
#                         "duration": "5 minutes",
#                         "activities": ["Quick quiz or discussion"]
#                     }
#                 },
#                 "key_concepts": [f"Key concepts related to {topic}"],
#                 "homework_assignment": f"Complete exercises related to {topic}",
#                 "additional_resources": ["Online resources", "Recommended readings"],
#                 "error": "Generated with fallback structure"
#             }
            
#     except json.JSONDecodeError as e:
#         # Return a structured fallback if JSON parsing fails
#         return {
#             "title": f"Lesson Plan: {topic}",
#             "topic": topic,
#             "grade_level": grade_level,
#             "duration": duration,
#             "learning_objectives": [
#                 f"Understand the fundamentals of {topic}",
#                 f"Apply {topic} concepts in real-world scenarios",
#                 f"Evaluate and analyze {topic} information"
#             ],
#             "materials_needed": ["Whiteboard", "Presentation slides", "Student handouts"],
#             "lesson_structure": {
#                 "introduction": {
#                     "duration": "10 minutes",
#                     "activities": [f"Warm-up activity introducing {topic}"]
#                 },
#                 "main_content": {
#                     "duration": "35 minutes",
#                     "activities": [
#                         f"Lecture on {topic} fundamentals",
#                         f"Interactive {topic} demonstration",
#                         f"Group activity exploring {topic}"
#                     ]
#                 },
#                 "conclusion": {
#                     "duration": "10 minutes",
#                     "activities": ["Review key points", "Q&A session"]
#                 },
#                 "assessment": {
#                     "duration": "5 minutes",
#                     "activities": ["Exit ticket or quick assessment"]
#                 }
#             },
#             "key_concepts": [f"Core principles of {topic}"],
#             "homework_assignment": f"Research and write about {topic} applications",
#             "additional_resources": ["Textbook chapters", "Online videos", "Practice worksheets"],
#             "error": f"JSON parsing failed: {str(e)}"
#         }
#     except Exception as e:
#         # Return error information
#         return {
#             "title": f"Lesson Plan: {topic}",
#             "topic": topic,
#             "grade_level": grade_level,
#             "duration": duration,
#             "error": f"Failed to generate lesson plan: {str(e)}"
#         }

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
# # print(res)

res2 = generate_lesson_plan("Python Programming", "Intermediate", "60 minutes", ["Understanding Python syntax", "Writing basic functions"])
# pprint(res2)

# with open('res2.txt', 'w') as file:
#     file.write(str(res2))

with open("res2.json", "w") as f:
    json.dump(res2, f, indent=4) # indent=4 for pretty printing

print("Formatted content successfully written to 'res2.json'")

# res3 = generate_flashcards("Python Programming", "Advanced", 5)
# print(res3)

# # formatting the output for better readability
# formatted_content = """
# res = generate_mcqs("Python Programming", "Intermediate", 5)
# {res}


# res2 = generate_lesson_plan("Python Programming", "Intermediate", "60 minutes", ["Understanding Python syntax", "Writing basic functions"])
# {res2}


# res3 = generate_flashcards("Python Programming", "Advanced", 5)
# {res3}
# """

# print("Formatted content:")
# print(formatted_content)

# # Write formatted version to another file
# with open('educhain_output_formatted.txt', 'a+') as file:
#     file.write(formatted_content)

# print("Formatted content successfully written to 'educhain_output_formatted.txt'")