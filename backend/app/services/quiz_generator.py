"""
Quiz Generation Service

This service generates various types of quiz questions from document content
using LLM-based question generation with quality validation.
"""

import asyncio
import json
import logging
import random
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

import openai
import structlog

from ..services.indexing_service import DocumentIndexingService

logger = structlog.get_logger(__name__)


class QuestionType(str, Enum):
    """Enum for different question types."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"


class DifficultyLevel(str, Enum):
    """Enum for difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuizQuestion(BaseModel):
    """Model for a quiz question."""
    id: str = Field(..., description="Unique identifier for the question")
    question_type: QuestionType
    question_text: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: Union[str, List[str]]  # Can be string or list for multiple correct answers
    explanation: str
    difficulty: DifficultyLevel
    topic: str
    source_content: str = Field(..., description="Original content the question was based on")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuizGenerationRequest(BaseModel):
    """Model for quiz generation request."""
    topic: Optional[str] = None
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE])
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    num_questions: int = Field(default=10, ge=1, le=50)
    content_filter: Optional[Dict[str, Any]] = None


class QuizGenerationService:
    """Service for generating quiz questions from indexed documents."""
    
    def __init__(
        self,
        openai_api_key: str,
        indexing_service: DocumentIndexingService,
        model: str = "gpt-3.5-turbo"
    ):
        """Initialize the quiz generation service."""
        self.openai_api_key = openai_api_key
        self.indexing_service = indexing_service
        self.model = model
        
        # Configure OpenAI
        openai.api_key = self.openai_api_key
        
        logger.info(
            "Quiz generation service initialized",
            model=model
        )
    
    async def generate_quiz(
        self,
        request: QuizGenerationRequest
    ) -> List[QuizQuestion]:
        """
        Generate a complete quiz based on the request parameters.
        
        Args:
            request: Quiz generation parameters
            
        Returns:
            List of generated quiz questions
        """
        try:
            logger.info(
                "Starting quiz generation",
                topic=request.topic,
                question_types=request.question_types,
                difficulty=request.difficulty_level,
                num_questions=request.num_questions
            )
            
            # Search for relevant content
            search_results = await self._search_relevant_content(
                topic=request.topic,
                filters=request.content_filter,
                limit=request.num_questions * 3  # Get more content for variety
            )
            
            if not search_results:
                raise ValueError("No relevant content found for quiz generation")
            
            # Generate questions for each type requested
            all_questions = []
            questions_per_type = max(1, request.num_questions // len(request.question_types))
            
            for question_type in request.question_types:
                questions = await self._generate_questions_by_type(
                    question_type=question_type,
                    content_chunks=search_results,
                    difficulty=request.difficulty_level,
                    num_questions=questions_per_type,
                    topic=request.topic or "General"
                )
                all_questions.extend(questions)
            
            # Trim to requested number and shuffle
            if len(all_questions) > request.num_questions:
                all_questions = random.sample(all_questions, request.num_questions)
            
            random.shuffle(all_questions)
            
            # Validate and filter questions
            validated_questions = await self._validate_questions(all_questions)
            
            logger.info(
                "Quiz generation completed",
                total_questions=len(validated_questions),
                question_types=[q.question_type for q in validated_questions]
            )
            
            return validated_questions
            
        except Exception as e:
            logger.error(
                "Quiz generation failed",
                error=str(e),
                request=request.dict()
            )
            raise
    
    async def _search_relevant_content(
        self,
        topic: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Search for relevant content for quiz generation."""
        try:
            # Use topic as search query if provided, otherwise get diverse content
            query = topic if topic else "concepts definitions examples"
            
            search_results = await self.indexing_service.search_documents(
                query=query,
                limit=limit,
                filters=filters
            )
            
            # Prioritize content with examples, definitions, and key concepts
            prioritized_results = []
            for result in search_results:
                metadata = result.get('metadata', {})
                priority_score = 0
                
                if metadata.get('is_definition'):
                    priority_score += 3
                if metadata.get('is_example'):
                    priority_score += 2
                if metadata.get('concept_keywords'):
                    priority_score += 1
                
                result['priority_score'] = priority_score
                prioritized_results.append(result)
            
            # Sort by priority and similarity score
            prioritized_results.sort(
                key=lambda x: (x['priority_score'], x.get('score', 0)),
                reverse=True
            )
            
            return prioritized_results
            
        except Exception as e:
            logger.error("Failed to search relevant content", error=str(e))
            return []
    
    async def _generate_questions_by_type(
        self,
        question_type: QuestionType,
        content_chunks: List[Dict[str, Any]],
        difficulty: DifficultyLevel,
        num_questions: int,
        topic: str
    ) -> List[QuizQuestion]:
        """Generate questions of a specific type."""
        questions = []
        
        # Select diverse content chunks
        selected_chunks = self._select_diverse_chunks(content_chunks, num_questions * 2)
        
        for chunk in selected_chunks[:num_questions]:
            try:
                question = await self._generate_single_question(
                    question_type=question_type,
                    content=chunk['text'],
                    difficulty=difficulty,
                    topic=topic,
                    metadata=chunk.get('metadata', {})
                )
                
                if question:
                    questions.append(question)
                    
            except Exception as e:
                logger.warning(
                    "Failed to generate question from chunk",
                    error=str(e),
                    question_type=question_type
                )
                continue
        
        return questions
    
    def _select_diverse_chunks(
        self,
        chunks: List[Dict[str, Any]],
        num_chunks: int
    ) -> List[Dict[str, Any]]:
        """Select diverse content chunks for question generation."""
        if len(chunks) <= num_chunks:
            return chunks
        
        # Group chunks by source document and page
        grouped_chunks = {}
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            key = f"{metadata.get('file_name', 'unknown')}_{metadata.get('page_number', 0)}"
            if key not in grouped_chunks:
                grouped_chunks[key] = []
            grouped_chunks[key].append(chunk)
        
        # Select chunks from different sources/pages for diversity
        selected = []
        chunk_groups = list(grouped_chunks.values())
        
        while len(selected) < num_chunks and chunk_groups:
            for group in chunk_groups[:]:
                if len(selected) >= num_chunks:
                    break
                if group:
                    selected.append(group.pop(0))
                if not group:
                    chunk_groups.remove(group)
        
        return selected
    
    async def _generate_single_question(
        self,
        question_type: QuestionType,
        content: str,
        difficulty: DifficultyLevel,
        topic: str,
        metadata: Dict[str, Any]
    ) -> Optional[QuizQuestion]:
        """Generate a single question from content."""
        try:
            if question_type == QuestionType.MULTIPLE_CHOICE:
                return await self._generate_multiple_choice(content, difficulty, topic, metadata)
            elif question_type == QuestionType.TRUE_FALSE:
                return await self._generate_true_false(content, difficulty, topic, metadata)
            elif question_type == QuestionType.FILL_IN_BLANK:
                return await self._generate_fill_in_blank(content, difficulty, topic, metadata)
            elif question_type == QuestionType.SHORT_ANSWER:
                return await self._generate_short_answer(content, difficulty, topic, metadata)
            else:
                raise ValueError(f"Unsupported question type: {question_type}")
                
        except Exception as e:
            logger.error(
                "Failed to generate single question",
                error=str(e),
                question_type=question_type
            )
            return None
    
    async def _generate_multiple_choice(
        self,
        content: str,
        difficulty: DifficultyLevel,
        topic: str,
        metadata: Dict[str, Any]
    ) -> Optional[QuizQuestion]:
        """Generate a multiple choice question."""
        
        difficulty_prompts = {
            DifficultyLevel.BEGINNER: "basic understanding and recall",
            DifficultyLevel.INTERMEDIATE: "comprehension and application",
            DifficultyLevel.ADVANCED: "analysis, synthesis, and evaluation"
        }
        
        prompt = f"""
Based on the following content, create a multiple choice question that tests {difficulty_prompts[difficulty]}.

Content:
{content[:1500]}

Requirements:
1. Create a clear, specific question
2. Provide 4 answer options (A, B, C, D)
3. Only one option should be correct
4. Incorrect options should be plausible but clearly wrong
5. Include a detailed explanation for the correct answer
6. Focus on {topic} concepts

Return the response in this exact JSON format:
{{
    "question": "Your question here",
    "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
    "correct_answer": "A",
    "explanation": "Detailed explanation of why this answer is correct and others are wrong"
}}
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return QuizQuestion(
                id=f"mc_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text=result["question"],
                options=result["options"],
                correct_answer=result["correct_answer"],
                explanation=result["explanation"],
                difficulty=difficulty,
                topic=topic,
                source_content=content[:500],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to generate multiple choice question", error=str(e))
            return None
    
    async def _generate_true_false(
        self,
        content: str,
        difficulty: DifficultyLevel,
        topic: str,
        metadata: Dict[str, Any]
    ) -> Optional[QuizQuestion]:
        """Generate a true/false question."""
        
        prompt = f"""
Based on the following content, create a true/false question about {topic}.

Content:
{content[:1500]}

Requirements:
1. Create a clear statement that can be definitively true or false
2. The statement should test understanding of key concepts
3. Avoid trivial or trick questions
4. Include a detailed explanation

Return the response in this exact JSON format:
{{
    "statement": "Your true/false statement here",
    "correct_answer": "true" or "false",
    "explanation": "Detailed explanation of why this is true or false"
}}
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return QuizQuestion(
                id=f"tf_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
                question_type=QuestionType.TRUE_FALSE,
                question_text=result["statement"],
                options=["True", "False"],
                correct_answer=result["correct_answer"].lower(),
                explanation=result["explanation"],
                difficulty=difficulty,
                topic=topic,
                source_content=content[:500],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to generate true/false question", error=str(e))
            return None
    
    async def _generate_fill_in_blank(
        self,
        content: str,
        difficulty: DifficultyLevel,
        topic: str,
        metadata: Dict[str, Any]
    ) -> Optional[QuizQuestion]:
        """Generate a fill-in-the-blank question."""
        
        prompt = f"""
Based on the following content, create a fill-in-the-blank question about {topic}.

Content:
{content[:1500]}

Requirements:
1. Select an important sentence from the content
2. Replace 1-2 key terms with blanks (_______)
3. The missing terms should be important concepts or facts
4. Include the correct answers
5. Provide explanation of the concepts

Return the response in this exact JSON format:
{{
    "question": "Sentence with _______ blanks",
    "correct_answers": ["answer1", "answer2"],
    "explanation": "Explanation of the missing terms and their importance"
}}
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return QuizQuestion(
                id=f"fib_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
                question_type=QuestionType.FILL_IN_BLANK,
                question_text=result["question"],
                correct_answer=result["correct_answers"],
                explanation=result["explanation"],
                difficulty=difficulty,
                topic=topic,
                source_content=content[:500],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Failed to generate fill-in-blank question", error=str(e))
            return None
    
    async def _generate_short_answer(
        self,
        content: str,
        difficulty: DifficultyLevel,
        topic: str,
        metadata: Dict[str, Any]
    ) -> Optional[QuizQuestion]:
        """Generate a short answer question."""
        
        difficulty_prompts = {
            DifficultyLevel.BEGINNER: "explain basic concepts",
            DifficultyLevel.INTERMEDIATE: "analyze relationships and applications",
            DifficultyLevel.ADVANCED: "synthesize complex ideas and evaluate approaches"
        }
        
        prompt = f"""
Based on the following content, create a short answer question that asks students to {difficulty_prompts[difficulty]} about {topic}.

Content:
{content[:1500]}

Requirements:
1. Create an open-ended question requiring 2-4 sentences to answer
2. Focus on understanding rather than memorization
3. Provide a comprehensive model answer
4. Include key points that should be covered

Return the response in this exact JSON format:
{{
    "question": "Your short answer question here",
    "model_answer": "Comprehensive model answer with key points",
    "key_points": ["point1", "point2", "point3"],
    "explanation": "What this question tests and why it's important"
}}
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return QuizQuestion(
                id=f"sa_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
                question_type=QuestionType.SHORT_ANSWER,
                question_text=result["question"],
                correct_answer=result["model_answer"],
                explanation=result["explanation"],
                difficulty=difficulty,
                topic=topic,
                source_content=content[:500],
                metadata={
                    **metadata,
                    "key_points": result["key_points"]
                }
            )
            
        except Exception as e:
            logger.error("Failed to generate short answer question", error=str(e))
            return None
    
    async def _validate_questions(
        self,
        questions: List[QuizQuestion]
    ) -> List[QuizQuestion]:
        """Validate and filter generated questions for quality."""
        validated_questions = []
        
        for question in questions:
            if await self._is_valid_question(question):
                validated_questions.append(question)
            else:
                logger.warning(
                    "Question failed validation",
                    question_id=question.id,
                    question_type=question.question_type
                )
        
        return validated_questions
    
    async def _is_valid_question(self, question: QuizQuestion) -> bool:
        """Check if a question meets quality criteria."""
        try:
            # Basic content checks
            if not question.question_text or len(question.question_text.strip()) < 10:
                return False
            
            if not question.correct_answer:
                return False
            
            if not question.explanation or len(question.explanation.strip()) < 20:
                return False
            
            # Question type specific validation
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                if not question.options or len(question.options) != 4:
                    return False
                
                # Check if correct answer is valid
                valid_answers = ['A', 'B', 'C', 'D']
                if question.correct_answer not in valid_answers:
                    return False
            
            elif question.question_type == QuestionType.TRUE_FALSE:
                if question.correct_answer.lower() not in ['true', 'false']:
                    return False
            
            elif question.question_type == QuestionType.FILL_IN_BLANK:
                if '____' not in question.question_text:
                    return False
                
                if not isinstance(question.correct_answer, list) or not question.correct_answer:
                    return False
            
            # Check for question uniqueness (basic duplicate detection)
            question_words = set(question.question_text.lower().split())
            if len(question_words) < 5:  # Too short/generic
                return False
            
            return True
            
        except Exception as e:
            logger.error("Question validation failed", error=str(e))
            return False
    
    async def assess_difficulty(
        self,
        question: QuizQuestion,
        content: str
    ) -> DifficultyLevel:
        """Assess the difficulty level of a generated question."""
        
        prompt = f"""
Assess the difficulty level of this question based on the source content.

Question: {question.question_text}
Question Type: {question.question_type}
Source Content: {content[:800]}

Consider:
1. Cognitive complexity (recall, understanding, application, analysis)
2. Concept abstraction level
3. Required prior knowledge
4. Problem-solving complexity

Return only one word: "beginner", "intermediate", or "advanced"
"""
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )
            
            difficulty_text = response.choices[0].message.content.strip().lower()
            
            if difficulty_text in ['beginner', 'easy', 'basic']:
                return DifficultyLevel.BEGINNER
            elif difficulty_text in ['advanced', 'hard', 'complex']:
                return DifficultyLevel.ADVANCED
            else:
                return DifficultyLevel.INTERMEDIATE
                
        except Exception as e:
            logger.error("Difficulty assessment failed", error=str(e))
            return DifficultyLevel.INTERMEDIATE


def get_quiz_generator(
    openai_api_key: str,
    indexing_service: DocumentIndexingService
) -> QuizGenerationService:
    """Factory function to create quiz generation service."""
    return QuizGenerationService(
        openai_api_key=openai_api_key,
        indexing_service=indexing_service
    ) 