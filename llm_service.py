"""
LLM service for generating questions and answers using OpenAI.
"""
import os
from openai import OpenAI
from typing import List
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
    
    def generate_questions(self, summary: str, num_questions: int = 5) -> List[str]:
        """
        Generate test questions based on the summary provided.
        
        Args:
            summary: The summary/context for question generation
            num_questions: Number of questions to generate (default: 5)
            
        Returns:
            List of generated questions
        """
        prompt = f"""Based on the following summary, generate {num_questions} well-structured test questions.

Summary:
{summary}

Generate questions that:
1. Are clear and specific
2. Test understanding of the key concepts
3. Are appropriate for assessment purposes
4. Cover different aspects of the topic

Return each question on a separate line, numbered from 1 to {num_questions}.
Only return the questions, no additional text or explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating test questions for educational assessments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            questions_text = response.choices[0].message.content.strip()
            # Parse questions from the response
            questions = []
            for line in questions_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering (e.g., "1. " or "- ")
                    question = line.lstrip('0123456789.- ').strip()
                    if question:
                        questions.append(question)
            
            # If parsing failed, split by newlines and clean
            if not questions:
                questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            return questions[:num_questions]  # Ensure we don't return more than requested
            
        except Exception as e:
            raise Exception(f"Error generating questions: {str(e)}")
    
    def generate_answer(self, question: str, summary: str) -> str:
        """
        Generate an answer for a given question based on the summary.
        
        Args:
            question: The question to answer
            summary: The summary/context for answer generation
            
        Returns:
            Generated answer text
        """
        prompt = f"""Based on the following summary, provide a clear and comprehensive answer to the question.

Summary:
{summary}

Question:
{question}

Provide a well-structured answer that:
1. Directly addresses the question
2. Is based on the information in the summary
3. Is clear and comprehensive
4. Is appropriate for an educational context"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at providing clear and educational answers to test questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Error generating answer: {str(e)}")

