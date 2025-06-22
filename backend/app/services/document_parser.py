"""
PDF Document Parser Service

This service handles PDF document processing including text extraction,
metadata extraction, text cleaning, and chunking strategies optimized
for quiz generation.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import pypdf
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Chunking strategies for different content types"""
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence" 
    SEMANTIC = "semantic"
    FIXED_SIZE = "fixed_size"
    TOPIC_BASED = "topic_based"


@dataclass
class DocumentMetadata:
    """Document metadata container"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    pages: int = 0
    file_size: int = 0
    language: Optional[str] = None


@dataclass
class DocumentChunk:
    """Document chunk with metadata"""
    content: str
    chunk_id: str
    page_number: int
    chunk_index: int
    chunk_type: str
    word_count: int
    concept_keywords: List[str]
    difficulty_indicators: List[str]
    is_definition: bool = False
    is_example: bool = False
    is_code_snippet: bool = False


@dataclass
class ProcessedDocument:
    """Complete processed document container"""
    metadata: DocumentMetadata
    chunks: List[DocumentChunk]
    key_concepts: List[str]
    definitions: Dict[str, str]
    examples: List[str]
    total_chunks: int
    processing_time: float


class DocumentParser:
    """PDF Document Parser with advanced text processing capabilities"""
    
    def __init__(self):
        self.concept_patterns = self._initialize_concept_patterns()
        self.definition_patterns = self._initialize_definition_patterns()
        self.example_patterns = self._initialize_example_patterns()
        
    def _initialize_concept_patterns(self) -> List[re.Pattern]:
        """Initialize regex patterns for concept identification"""
        patterns = [
            re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'),  # Title case terms
            re.compile(r'\b\w+(?:-\w+)*\b'),  # Hyphenated terms
            re.compile(r'\b[A-Z]{2,}\b'),  # Acronyms
        ]
        return patterns
    
    def _initialize_definition_patterns(self) -> List[re.Pattern]:
        """Initialize regex patterns for definition identification"""
        patterns = [
            re.compile(r'(.+?)\s+is\s+(?:a|an|the)?\s*(.+?)(?:\.|,|;)', re.IGNORECASE),
            re.compile(r'(.+?)\s+refers\s+to\s+(.+?)(?:\.|,|;)', re.IGNORECASE),
            re.compile(r'(.+?)\s+means\s+(.+?)(?:\.|,|;)', re.IGNORECASE),
            re.compile(r'(.+?):\s+(.+?)(?:\.|,|;)', re.IGNORECASE),
            re.compile(r'Definition:\s*(.+?)(?:\.|,|;)', re.IGNORECASE),
        ]
        return patterns
    
    def _initialize_example_patterns(self) -> List[re.Pattern]:
        """Initialize regex patterns for example identification"""
        patterns = [
            re.compile(r'(?:for example|e\.g\.|such as|including|like)(.+?)(?:\.|,|;)', re.IGNORECASE),
            re.compile(r'Example\s*\d*:\s*(.+?)(?:\n|$)', re.IGNORECASE),
            re.compile(r'Consider\s+(.+?)(?:\.|,|;)', re.IGNORECASE),
        ]
        return patterns

    def parse_pdf(self, file_path: str) -> ProcessedDocument:
        """
        Parse a PDF file and extract structured content
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ProcessedDocument with all extracted information
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting PDF parsing for: {file_path}")
        
        try:
            # Extract metadata and text
            metadata = self._extract_metadata(file_path)
            raw_text, page_texts = self._extract_text(file_path)
            
            if not raw_text.strip():
                raise ValueError("No text content extracted from PDF")
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(raw_text)
            
            # Extract key information
            key_concepts = self._extract_key_concepts(cleaned_text)
            definitions = self._extract_definitions(cleaned_text)
            examples = self._extract_examples(cleaned_text)
            
            # Create chunks
            chunks = self._create_chunks(
                page_texts, 
                strategy=ChunkingStrategy.SEMANTIC,
                key_concepts=key_concepts
            )
            
            processing_time = time.time() - start_time
            
            processed_doc = ProcessedDocument(
                metadata=metadata,
                chunks=chunks,
                key_concepts=key_concepts,
                definitions=definitions,
                examples=examples,
                total_chunks=len(chunks),
                processing_time=processing_time
            )
            
            logger.info(f"PDF parsing completed in {processing_time:.2f} seconds")
            logger.info(f"Extracted {len(chunks)} chunks, {len(key_concepts)} concepts, {len(definitions)} definitions")
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise

    def _extract_metadata(self, file_path: str) -> DocumentMetadata:
        """Extract metadata from PDF file"""
        try:
            reader = PdfReader(file_path)
            metadata = reader.metadata or {}
            file_size = Path(file_path).stat().st_size
            
            return DocumentMetadata(
                title=metadata.get('/Title'),
                author=metadata.get('/Author'),
                subject=metadata.get('/Subject'),
                creator=metadata.get('/Creator'),
                producer=metadata.get('/Producer'),
                creation_date=str(metadata.get('/CreationDate', '')),
                modification_date=str(metadata.get('/ModDate', '')),
                pages=len(reader.pages),
                file_size=file_size,
                language=metadata.get('/Language')
            )
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            return DocumentMetadata(pages=0, file_size=0)

    def _extract_text(self, file_path: str) -> Tuple[str, List[str]]:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file_path)
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"\n--- Page {page_num + 1} ---\n" + page_text
                        page_texts.append(page_text)
                    else:
                        page_texts.append("")
                        logger.warning(f"No text extracted from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    page_texts.append("")
            
            return full_text, page_texts
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess extracted text"""
        # Remove excessive whitespace and page markers
        text = re.sub(r'\n--- Page \d+ ---\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'\x0c', '', text)  # Form feed characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Non-ASCII characters
        
        # Normalize punctuation
        text = re.sub(r'[""]', '"', text)
        text = re.sub(r'['']', "'", text)
        
        return text.strip()

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        concepts = set()
        
        # Use pattern matching to find concepts
        for pattern in self.concept_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match) > 2:
                    concepts.add(match.strip())
        
        # Filter and rank concepts by frequency
        concept_freq = {}
        for concept in concepts:
            count = text.lower().count(concept.lower())
            if count > 1:  # Only keep concepts that appear multiple times
                concept_freq[concept] = count
        
        # Return top concepts sorted by frequency
        sorted_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)
        return [concept for concept, _ in sorted_concepts[:50]]  # Top 50 concepts

    def _extract_definitions(self, text: str) -> Dict[str, str]:
        """Extract definitions from text"""
        definitions = {}
        
        for pattern in self.definition_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    term = match[0].strip()
                    definition = match[1].strip()
                    if len(term) > 2 and len(definition) > 10:
                        definitions[term] = definition
                elif isinstance(match, str):
                    # For single group patterns like "Definition: ..."
                    if len(match) > 10:
                        definitions[f"Definition {len(definitions) + 1}"] = match.strip()
        
        return definitions

    def _extract_examples(self, text: str) -> List[str]:
        """Extract examples from text"""
        examples = []
        
        for pattern in self.example_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 10:
                    examples.append(match.strip())
        
        return examples[:20]  # Limit to 20 examples

    def _create_chunks(
        self, 
        page_texts: List[str], 
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        max_chunk_size: int = 1000,
        overlap: int = 100,
        key_concepts: List[str] = None
    ) -> List[DocumentChunk]:
        """Create document chunks using specified strategy"""
        
        chunks = []
        chunk_id_counter = 0
        
        for page_num, page_text in enumerate(page_texts):
            if not page_text.strip():
                continue
                
            page_chunks = self._chunk_page(
                page_text, 
                page_num + 1, 
                strategy, 
                max_chunk_size, 
                overlap,
                key_concepts or []
            )
            
            for chunk in page_chunks:
                chunk.chunk_id = f"chunk_{chunk_id_counter:04d}"
                chunk.chunk_index = chunk_id_counter
                chunks.append(chunk)
                chunk_id_counter += 1
        
        return chunks

    def _chunk_page(
        self,
        page_text: str,
        page_number: int,
        strategy: ChunkingStrategy,
        max_chunk_size: int,
        overlap: int,
        key_concepts: List[str]
    ) -> List[DocumentChunk]:
        """Chunk a single page using the specified strategy"""
        
        if strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(page_text, page_number, key_concepts)
        elif strategy == ChunkingStrategy.SEMANTIC:
            return self._chunk_by_semantic(page_text, page_number, max_chunk_size, key_concepts)
        elif strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_by_fixed_size(page_text, page_number, max_chunk_size, overlap, key_concepts)
        else:
            return self._chunk_by_semantic(page_text, page_number, max_chunk_size, key_concepts)

    def _chunk_by_paragraph(self, text: str, page_number: int, key_concepts: List[str]) -> List[DocumentChunk]:
        """Chunk text by paragraphs"""
        paragraphs = text.split('\n\n')
        chunks = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:  # Skip very short paragraphs
                chunk = self._create_document_chunk(
                    content=para,
                    page_number=page_number,
                    chunk_type="paragraph",
                    key_concepts=key_concepts
                )
                chunks.append(chunk)
        
        return chunks

    def _chunk_by_semantic(self, text: str, page_number: int, max_chunk_size: int, key_concepts: List[str]) -> List[DocumentChunk]:
        """Chunk text by semantic boundaries (headings, topics)"""
        # Look for section headers and topic boundaries
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        current_topic = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a heading/section marker
            is_heading = (
                line.isupper() or
                re.match(r'^[A-Z][^a-z]*$', line) or
                re.match(r'^\d+\.?\s+[A-Z]', line) or
                len(line) < 50 and not line.endswith('.')
            )
            
            if is_heading and current_chunk:
                # Save current chunk
                chunk = self._create_document_chunk(
                    content=current_chunk.strip(),
                    page_number=page_number,
                    chunk_type=f"section_{current_topic}" if current_topic else "section",
                    key_concepts=key_concepts
                )
                chunks.append(chunk)
                current_chunk = line
                current_topic = line[:30]  # Use first part as topic
            else:
                current_chunk += "\n" + line if current_chunk else line
                
                # Check size limit
                if len(current_chunk) > max_chunk_size:
                    chunk = self._create_document_chunk(
                        content=current_chunk.strip(),
                        page_number=page_number,
                        chunk_type=f"section_{current_topic}" if current_topic else "section",
                        key_concepts=key_concepts
                    )
                    chunks.append(chunk)
                    current_chunk = ""
        
        if current_chunk.strip():
            chunk = self._create_document_chunk(
                content=current_chunk.strip(),
                page_number=page_number,
                chunk_type=f"section_{current_topic}" if current_topic else "section",
                key_concepts=key_concepts
            )
            chunks.append(chunk)
        
        return chunks

    def _chunk_by_fixed_size(self, text: str, page_number: int, max_chunk_size: int, overlap: int, key_concepts: List[str]) -> List[DocumentChunk]:
        """Chunk text by fixed size with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                if last_period > len(chunk_text) * 0.7:  # If period is in last 30%
                    chunk_text = chunk_text[:last_period + 1]
                    end = start + len(chunk_text)
            
            chunk = self._create_document_chunk(
                content=chunk_text.strip(),
                page_number=page_number,
                chunk_type="fixed_size",
                key_concepts=key_concepts
            )
            chunks.append(chunk)
            
            start = end - overlap
        
        return chunks

    def _create_document_chunk(self, content: str, page_number: int, chunk_type: str, key_concepts: List[str]) -> DocumentChunk:
        """Create a DocumentChunk with metadata"""
        # Count words (basic word count)
        word_count = len(content.split())
        
        # Find concept keywords in this chunk
        chunk_concepts = []
        content_lower = content.lower()
        for concept in key_concepts:
            if concept.lower() in content_lower:
                chunk_concepts.append(concept)
        
        # Identify difficulty indicators
        difficulty_indicators = self._identify_difficulty_indicators(content)
        
        # Check if chunk contains definitions, examples, or code
        is_definition = any(pattern.search(content) for pattern in self.definition_patterns)
        is_example = any(pattern.search(content) for pattern in self.example_patterns)
        is_code_snippet = self._is_code_snippet(content)
        
        return DocumentChunk(
            content=content,
            chunk_id="",  # Will be set later
            page_number=page_number,
            chunk_index=0,  # Will be set later
            chunk_type=chunk_type,
            word_count=word_count,
            concept_keywords=chunk_concepts,
            difficulty_indicators=difficulty_indicators,
            is_definition=is_definition,
            is_example=is_example,
            is_code_snippet=is_code_snippet
        )

    def _identify_difficulty_indicators(self, content: str) -> List[str]:
        """Identify indicators of content difficulty"""
        indicators = []
        
        # Technical terms
        if re.search(r'\b(?:algorithm|implementation|optimization|architecture)\b', content, re.IGNORECASE):
            indicators.append("technical")
        
        # Advanced concepts
        if re.search(r'\b(?:advanced|complex|sophisticated|comprehensive)\b', content, re.IGNORECASE):
            indicators.append("advanced")
        
        # Mathematical content
        if re.search(r'[∑∫∂∆π∞≤≥≠±]|∂|∫|∑', content):
            indicators.append("mathematical")
        
        # Code-related
        if re.search(r'[{}()\[\];]|def |class |import |function|method', content):
            indicators.append("programming")
        
        return indicators

    def _is_code_snippet(self, content: str) -> bool:
        """Determine if content is a code snippet"""
        code_indicators = [
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*[:\(]',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'[{}()\[\]]{.*}',
            r'[a-zA-Z_]\w*\s*=\s*[^=]',
            r'if\s+.*:\s*$',
            r'for\s+\w+\s+in\s+',
            r'while\s+.*:\s*$'
        ]
        
        for pattern in code_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        
        return False


# Utility functions for external use
def parse_pdf_file(file_path: str) -> ProcessedDocument:
    """Convenience function to parse a single PDF file"""
    parser = DocumentParser()
    return parser.parse_pdf(file_path)


def get_document_summary(processed_doc: ProcessedDocument) -> Dict[str, Any]:
    """Get a summary of processed document"""
    return {
        "title": processed_doc.metadata.title,
        "pages": processed_doc.metadata.pages,
        "total_chunks": processed_doc.total_chunks,
        "key_concepts_count": len(processed_doc.key_concepts),
        "definitions_count": len(processed_doc.definitions),
        "examples_count": len(processed_doc.examples),
        "processing_time": processed_doc.processing_time,
        "chunk_types": list(set(chunk.chunk_type for chunk in processed_doc.chunks))
    }
