import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from educhain import Educhain, LLMConfig
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Educhain client with Gemini
try:
    client = Educhain(
        LLMConfig(
            custom_model=ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=os.getenv("GEMINI_API_KEY")
            )
        )
    )
    logger.info("Educhain client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Educhain client: {e}")
    raise

mcp = FastMCP("Educhain MCP Server")

@mcp.tool()
def generate_mcqs(topic: str, level: str = "Beginner", num: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create multiple-choice questions for <topic> at the given difficulty <level>.
    Returns a list of question dictionaries that Claude can read.
    """
    try:
        logger.info(f"Generating {num} MCQs for topic: {topic}, level: {level}")
        
        # Generate questions using Educhain
        result = client.qna_engine.generate_questions(
            topic=topic, 
            num=num, 
            question_type="Multiple Choice", 
            difficulty_level=level
        )
        
        # Convert to dict and extract questions
        result_dict = result.model_dump()
        questions = result_dict.get("questions", [])
        
        # Validate that we got a list
        if not isinstance(questions, list):
            logger.error(f"Expected list of questions, got: {type(questions)}")
            return {"result": []}
        
        # Ensure each question has the required fields
        validated_questions = []
        for q in questions:
            if isinstance(q, dict) and "question" in q:
                validated_questions.append(q)
            else:
                logger.warning(f"Skipping invalid question: {q}")
        
        logger.info(f"Successfully generated {len(validated_questions)} questions")
        return {"result": validated_questions}
        
    except Exception as e:
        logger.error(f"Error generating MCQs: {e}")
        return {"result": []}

@mcp.tool()
def generate_lesson_plan(
    topic: str, 
    grade_level: str = "Beginner", 
    duration: str = "60 minutes",
    learning_objectives: str = "Understanding the process, Identifying key components"
) -> Dict[str, Any]:
    """
    Build a structured lesson plan for <topic> at <grade_level>.
    """
    try:
        logger.info(f"Generating lesson plan for topic: {topic}, grade_level: {grade_level}")
        
        # Generate lesson plan using Educhain
        lesson = client.content_engine.generate_lesson_plan(topic=topic)
        
        # Convert to dict
        lesson_dict = lesson.model_dump() if hasattr(lesson, 'model_dump') else lesson
        
        # Ensure it's a dictionary
        if not isinstance(lesson_dict, dict):
            logger.error(f"Expected dict for lesson plan, got: {type(lesson_dict)}")
            return {
                "title": f"Lesson Plan: {topic}",
                "grade_level": grade_level,
                "duration": duration,
                "learning_objectives": learning_objectives,
                "error": "Failed to generate lesson plan"
            }
        
        # Add the requested metadata if not present
        lesson_dict.update({
            "grade_level": lesson_dict.get("grade_level", grade_level),
            "duration": lesson_dict.get("duration", duration),
            "learning_objectives": lesson_dict.get("learning_objectives", learning_objectives)
        })
        
        logger.info("Successfully generated lesson plan")
        return lesson_dict
        
    except Exception as e:
        logger.error(f"Error generating lesson plan: {e}")
        return {
            "title": f"Lesson Plan: {topic}",
            "grade_level": grade_level,
            "duration": duration,
            "learning_objectives": learning_objectives,
            "error": str(e)
        }

@mcp.tool()
def generate_flashcards(topic: str, level: str = "Beginner", num: int = 5) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate flashcards for <topic> at the given difficulty <level>.
    Returns a list of flashcard dictionaries with question and answer.
    """
    try:
        logger.info(f"Generating {num} flashcards for topic: {topic}, level: {level}")
        
        # Get MCQs first
        mcqs_result = generate_mcqs(topic, level, num)
        mcqs = mcqs_result.get("result", [])
        
        if not mcqs:
            logger.warning("No MCQs generated for flashcards")
            return {"result": []}
        
        # Convert MCQs to flashcards
        flashcards = []
        for q in mcqs:
            if isinstance(q, dict) and "question" in q and "answer" in q:
                flashcards.append({
                    "question": q["question"],
                    "answer": q["answer"]
                })
            else:
                logger.warning(f"Skipping invalid MCQ for flashcard: {q}")
        
        logger.info(f"Successfully generated {len(flashcards)} flashcards")
        return {"result": flashcards}
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return {"result": []}

if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise
