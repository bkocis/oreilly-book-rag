"""
Question Templates Service

This service provides structured templates and prompts for generating
different types of quiz questions from document content.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


class QuestionCategory(str, Enum):
    """Categories of questions based on learning objectives."""
    CONCEPT_BASED = "concept_based"
    APPLICATION_BASED = "application_based"
    SCENARIO_BASED = "scenario_based"
    CODE_BASED = "code_based"
    ANALYTICAL = "analytical"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"


class ContentType(str, Enum):
    """Types of content for specialized question generation."""
    PROGRAMMING = "programming"
    THEORY = "theory"
    PRACTICAL = "practical"
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"


@dataclass
class QuestionTemplate:
    """Template for generating questions."""
    category: QuestionCategory
    content_type: ContentType
    question_pattern: str
    answer_pattern: str
    explanation_pattern: str
    difficulty_indicators: Dict[str, List[str]]
    examples: List[Dict[str, Any]]


class QuestionTemplatesService:
    """Service for managing question templates and generation prompts."""
    
    def __init__(self):
        """Initialize the question templates service."""
        self.templates = self._initialize_templates()
        self.prompts = self._initialize_prompts()
        
        logger.info("Question templates service initialized")
    
    def _initialize_templates(self) -> Dict[str, QuestionTemplate]:
        """Initialize all question templates."""
        templates = {}
        
        # Concept-based templates
        templates["concept_definition"] = QuestionTemplate(
            category=QuestionCategory.CONCEPT_BASED,
            content_type=ContentType.CONCEPTUAL,
            question_pattern="What is {concept}?",
            answer_pattern="Definition and key characteristics of {concept}",
            explanation_pattern="Explain why this definition is accurate and important",
            difficulty_indicators={
                "beginner": ["basic definition", "simple explanation", "fundamental"],
                "intermediate": ["detailed explanation", "relationships", "applications"],
                "advanced": ["nuanced understanding", "edge cases", "expert perspective"]
            },
            examples=[
                {
                    "question": "What is polymorphism in object-oriented programming?",
                    "answer": "The ability of objects to take multiple forms and respond differently to the same method call",
                    "explanation": "Polymorphism allows code to be more flexible and reusable by working with objects at a more abstract level"
                }
            ]
        )
        
        # Application-based templates
        templates["application_practical"] = QuestionTemplate(
            category=QuestionCategory.APPLICATION_BASED,
            content_type=ContentType.PRACTICAL,
            question_pattern="How would you use {concept} to solve {problem}?",
            answer_pattern="Step-by-step application with specific examples",
            explanation_pattern="Explain why this approach is effective",
            difficulty_indicators={
                "beginner": ["direct application", "clear steps"],
                "intermediate": ["adaptation required", "multiple approaches"],
                "advanced": ["optimization", "complex scenarios"]
            },
            examples=[]
        )
        
        # Scenario-based templates
        templates["scenario_problem_solving"] = QuestionTemplate(
            category=QuestionCategory.SCENARIO_BASED,
            content_type=ContentType.PRACTICAL,
            question_pattern="Given the scenario: {scenario}, what would you do?",
            answer_pattern="Systematic approach to solving the problem",
            explanation_pattern="Justify the chosen approach and consider alternatives",
            difficulty_indicators={
                "beginner": ["straightforward scenario", "clear solution"],
                "intermediate": ["complex scenario", "multiple factors"],
                "advanced": ["ambiguous scenario", "competing priorities"]
            },
            examples=[]
        )
        
        # Code-based templates
        templates["code_completion"] = QuestionTemplate(
            category=QuestionCategory.CODE_BASED,
            content_type=ContentType.PROGRAMMING,
            question_pattern="Complete this code to implement {functionality}: {partial_code}",
            answer_pattern="Complete working code with proper implementation",
            explanation_pattern="Explain the implementation choices and alternatives",
            difficulty_indicators={
                "beginner": ["fill in missing parts", "basic logic"],
                "intermediate": ["implement algorithms", "handle edge cases"],
                "advanced": ["optimize performance", "design patterns"]
            },
            examples=[]
        )
        
        return templates
    
    def _initialize_prompts(self) -> Dict[str, Dict[str, str]]:
        """Initialize system prompts for different question types."""
        return {
            "concept_based": {
                "system": """You are an expert educator creating concept-based quiz questions.
                Focus on testing understanding of definitions, relationships, and theoretical knowledge.
                Ensure questions are clear, unambiguous, and test genuine understanding rather than memorization.""",
                
                "user_template": """Based on this content: {content}
                
                Create a {difficulty} level {question_type} question that tests understanding of the key concept(s).
                The question should:
                1. Focus on the most important concept in the content
                2. Be appropriate for {difficulty} level learners
                3. Test genuine understanding, not just memorization
                4. Include a clear, educational explanation
                
                Topic: {topic}
                Content Type: {content_type}
                
                Return the response in this JSON format:
                {{
                    "question": "The actual question text",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "The correct answer",
                    "explanation": "Detailed explanation of why this is correct",
                    "key_concepts": ["concept1", "concept2"],
                    "difficulty_justification": "Why this question is at the specified difficulty level"
                }}"""
            },
            
            "application_based": {
                "system": """You are an expert educator creating application-based quiz questions.
                Focus on testing the ability to apply knowledge to solve real-world problems.
                Questions should require learners to use their knowledge practically.""",
                
                "user_template": """Based on this content: {content}
                
                Create a {difficulty} level {question_type} question that tests practical application of the concepts.
                The question should:
                1. Present a realistic scenario or problem
                2. Require applying the concepts from the content
                3. Be appropriate for {difficulty} level learners
                4. Include step-by-step explanation of the solution
                
                Topic: {topic}
                Content Type: {content_type}
                
                Return the response in this JSON format:
                {{
                    "question": "The practical scenario/problem question",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "The correct solution/approach",
                    "explanation": "Step-by-step explanation of how to solve this problem",
                    "key_concepts": ["concept1", "concept2"],
                    "practical_tips": "Additional tips for real-world application"
                }}"""
            },
            
            "scenario_based": {
                "system": """You are an expert educator creating scenario-based quiz questions.
                Focus on testing decision-making and problem-solving skills in realistic contexts.
                Questions should present complex situations requiring thoughtful analysis.""",
                
                "user_template": """Based on this content: {content}
                
                Create a {difficulty} level {question_type} question that presents a realistic scenario.
                The question should:
                1. Present a complex, realistic situation
                2. Require analysis and decision-making
                3. Have multiple valid considerations
                4. Be appropriate for {difficulty} level learners
                
                Topic: {topic}
                Content Type: {content_type}
                
                Return the response in this JSON format:
                {{
                    "question": "The scenario and question",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "The best solution/approach",
                    "explanation": "Analysis of the scenario and justification for the solution",
                    "alternative_approaches": "Other valid approaches and their trade-offs",
                    "key_considerations": ["factor1", "factor2"]
                }}"""
            },
            
            "code_based": {
                "system": """You are an expert programming educator creating code-based quiz questions.
                Focus on testing programming knowledge, code comprehension, and implementation skills.
                Questions should be practical and relevant to real programming scenarios.""",
                
                "user_template": """Based on this content: {content}
                
                Create a {difficulty} level {question_type} question that involves code.
                The question should:
                1. Include actual code snippets when relevant
                2. Test programming concepts and skills
                3. Be syntactically correct and runnable
                4. Include proper code formatting and comments
                
                Topic: {topic}
                Content Type: {content_type}
                Programming Language: {programming_language}
                
                Return the response in this JSON format:
                {{
                    "question": "The code-based question with proper formatting",
                    "code_snippet": "Any code included in the question (if applicable)",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "The correct code/solution",
                    "explanation": "Technical explanation of the code and concepts",
                    "common_mistakes": "Common errors students make with this concept",
                    "best_practices": "Relevant coding best practices"
                }}"""
            }
        }
    
    def get_template(
        self,
        category: QuestionCategory,
        content_type: ContentType
    ) -> Optional[QuestionTemplate]:
        """Get a specific question template."""
        template_key = f"{category.value}_{content_type.value}"
        
        # Try exact match first
        if template_key in self.templates:
            return self.templates[template_key]
        
        # Try category-based match
        for key, template in self.templates.items():
            if template.category == category:
                return template
        
        return None
    
    def get_prompt(
        self,
        category: QuestionCategory,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Get system and user prompts for question generation.
        
        Args:
            category: Question category
            **kwargs: Template variables for prompt formatting
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        if category.value not in self.prompts:
            # Default to concept-based prompts
            category = QuestionCategory.CONCEPT_BASED
        
        prompt_config = self.prompts[category.value]
        system_prompt = prompt_config["system"]
        user_prompt = prompt_config["user_template"].format(**kwargs)
        
        return system_prompt, user_prompt
    
    def detect_content_type(self, content: str) -> ContentType:
        """
        Detect the content type based on content analysis.
        
        Args:
            content: The content to analyze
            
        Returns:
            Detected content type
        """
        content_lower = content.lower()
        
        # Programming indicators
        programming_keywords = [
            'function', 'class', 'method', 'variable', 'code', 'syntax',
            'algorithm', 'programming', 'script', 'import', 'library',
            'def ', 'class ', 'return', 'if ', 'for ', 'while ', 'try:'
        ]
        
        # Mathematical indicators
        math_keywords = [
            'equation', 'formula', 'calculate', 'mathematical', 'theorem',
            'proof', 'algebra', 'geometry', 'statistics', 'probability'
        ]
        
        # Theoretical indicators
        theory_keywords = [
            'theory', 'principle', 'concept', 'definition', 'abstract',
            'model', 'framework', 'paradigm', 'philosophy'
        ]
        
        # Procedural indicators
        procedural_keywords = [
            'step', 'process', 'procedure', 'workflow', 'method',
            'approach', 'technique', 'strategy', 'implementation'
        ]
        
        # Count keyword matches
        programming_score = sum(1 for kw in programming_keywords if kw in content_lower)
        math_score = sum(1 for kw in math_keywords if kw in content_lower)
        theory_score = sum(1 for kw in theory_keywords if kw in content_lower)
        procedural_score = sum(1 for kw in procedural_keywords if kw in content_lower)
        
        # Determine content type based on highest score
        scores = {
            ContentType.PROGRAMMING: programming_score,
            ContentType.MATHEMATICAL: math_score,
            ContentType.THEORY: theory_score,
            ContentType.PROCEDURAL: procedural_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return ContentType.CONCEPTUAL  # Default
        
        # Return the content type with highest score
        for content_type, score in scores.items():
            if score == max_score:
                return content_type
        
        return ContentType.CONCEPTUAL
    
    def suggest_question_categories(
        self,
        content: str,
        difficulty: str = "intermediate"
    ) -> List[QuestionCategory]:
        """
        Suggest appropriate question categories for given content.
        
        Args:
            content: The content to analyze
            difficulty: Target difficulty level
            
        Returns:
            List of suggested question categories
        """
        content_type = self.detect_content_type(content)
        content_lower = content.lower()
        
        suggestions = []
        
        # Always include concept-based for foundational understanding
        suggestions.append(QuestionCategory.CONCEPT_BASED)
        
        # Add application-based if content has practical elements
        if any(word in content_lower for word in ['example', 'use', 'apply', 'implement']):
            suggestions.append(QuestionCategory.APPLICATION_BASED)
        
        # Add scenario-based for intermediate/advanced levels
        if difficulty in ['intermediate', 'advanced']:
            suggestions.append(QuestionCategory.SCENARIO_BASED)
        
        # Add code-based for programming content
        if content_type == ContentType.PROGRAMMING:
            suggestions.append(QuestionCategory.CODE_BASED)
        
        # Add analytical for advanced content
        if difficulty == 'advanced':
            suggestions.append(QuestionCategory.ANALYTICAL)
        
        return suggestions
    
    def generate_explanation_prompt(
        self,
        question: str,
        correct_answer: str,
        content: str,
        category: QuestionCategory
    ) -> str:
        """
        Generate a prompt for creating detailed explanations.
        
        Args:
            question: The question text
            correct_answer: The correct answer
            content: Source content
            category: Question category
            
        Returns:
            Formatted explanation prompt
        """
        base_prompt = f"""
        Create a comprehensive explanation for this quiz question:
        
        Question: {question}
        Correct Answer: {correct_answer}
        Source Content: {content}
        
        The explanation should:
        1. Clearly explain why the correct answer is right
        2. Address common misconceptions
        3. Provide additional context from the source material
        4. Be educational and help reinforce learning
        """
        
        category_specific = {
            QuestionCategory.CONCEPT_BASED: "Focus on explaining the underlying concepts and their relationships.",
            QuestionCategory.APPLICATION_BASED: "Emphasize practical applications and real-world relevance.",
            QuestionCategory.SCENARIO_BASED: "Analyze the scenario and explain the decision-making process.",
            QuestionCategory.CODE_BASED: "Explain the code logic and programming concepts involved.",
            QuestionCategory.ANALYTICAL: "Break down the analytical process and reasoning steps."
        }
        
        if category in category_specific:
            base_prompt += f"\n5. {category_specific[category]}"
        
        return base_prompt.strip()


def get_question_templates_service() -> QuestionTemplatesService:
    """Get a singleton instance of the question templates service."""
    return QuestionTemplatesService() 