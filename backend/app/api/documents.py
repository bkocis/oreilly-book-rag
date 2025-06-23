"""
Document Processing API endpoints for O'Reilly RAG Quiz system.

This module provides endpoints for document upload, processing, management,
and topic extraction functionality.
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import tempfile
import os

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from ..services.document_parser import DocumentParser, ProcessedDocument
from ..services.indexing_service import DocumentIndexingService, get_indexing_service

logger = structlog.get_logger(__name__)

# Initialize router
router = APIRouter()

# Global storage for processing tasks (in production, use Redis or database)
processing_tasks: Dict[str, Dict[str, Any]] = {}


# Pydantic models for API responses
class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool
    message: str
    task_id: str
    file_name: str
    file_size: int


class DocumentProcessingStatus(BaseModel):
    """Response model for document processing status."""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    file_name: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class DocumentMetadataResponse(BaseModel):
    """Response model for document metadata."""
    file_name: str
    file_path: str
    title: Optional[str] = None
    author: Optional[str] = None
    pages: int
    file_size: int
    indexed_at: Optional[str] = None
    topics: List[str] = []
    key_concepts: List[str] = []
    total_chunks: int = 0


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentMetadataResponse]
    total: int


class TopicExtractionRequest(BaseModel):
    """Request model for topic extraction."""
    text: str
    max_topics: int = Field(default=10, ge=1, le=50)


class TopicExtractionResponse(BaseModel):
    """Response model for topic extraction."""
    topics: List[str]
    concepts: List[str]
    processing_time: float


class DocumentDeletionResponse(BaseModel):
    """Response model for document deletion."""
    success: bool
    message: str
    file_name: str


# Helper functions
def generate_task_id() -> str:
    """Generate a unique task ID."""
    import uuid
    return str(uuid.uuid4())


async def process_document_background(
    task_id: str,
    file_path: str,
    file_name: str,
    indexing_service: DocumentIndexingService
):
    """Background task for document processing."""
    try:
        # Update task status
        processing_tasks[task_id].update({
            'status': 'processing',
            'progress': 10,
            'message': 'Parsing document...',
            'started_at': datetime.utcnow()
        })
        
        # Initialize document parser
        parser = DocumentParser()
        
        # Parse the document
        logger.info("Starting document parsing", file_path=file_path, task_id=task_id)
        processed_doc = parser.parse_pdf(file_path)
        
        processing_tasks[task_id].update({
            'progress': 50,
            'message': 'Indexing document...'
        })
        
        # Index the document
        logger.info("Starting document indexing", file_path=file_path, task_id=task_id)
        indexing_result = await indexing_service.index_document(
            file_path=file_path,
            metadata={
                'original_filename': file_name,
                'processed_at': datetime.utcnow().isoformat()
            }
        )
        
        # Prepare result
        result = {
            'file_name': file_name,
            'file_path': file_path,
            'metadata': {
                'title': processed_doc.metadata.title,
                'author': processed_doc.metadata.author,
                'pages': processed_doc.metadata.pages,
                'file_size': processed_doc.metadata.file_size,
                'language': processed_doc.metadata.language,
            },
            'processing_stats': {
                'total_chunks': processed_doc.total_chunks,
                'processing_time': processed_doc.processing_time,
                'key_concepts_count': len(processed_doc.key_concepts),
                'definitions_count': len(processed_doc.definitions),
                'examples_count': len(processed_doc.examples),
            },
            'key_concepts': processed_doc.key_concepts[:20],  # Limit to top 20
            'definitions': dict(list(processed_doc.definitions.items())[:10]),  # Limit to 10
            'indexing_result': indexing_result
        }
        
        # Update task as completed
        processing_tasks[task_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Document processed successfully',
            'completed_at': datetime.utcnow(),
            'result': result
        })
        
        logger.info(
            "Document processing completed",
            file_path=file_path,
            task_id=task_id,
            chunks=processed_doc.total_chunks,
            concepts=len(processed_doc.key_concepts)
        )
        
    except Exception as e:
        logger.error(
            "Document processing failed",
            file_path=file_path,
            task_id=task_id,
            error=str(e)
        )
        processing_tasks[task_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Processing failed: {str(e)}',
            'completed_at': datetime.utcnow(),
            'error': str(e)
        })
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info("Temporary file cleaned up", file_path=file_path)
        except Exception as e:
            logger.warning("Failed to clean up temporary file", file_path=file_path, error=str(e))


# API Endpoints
@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document to upload and process"),
    indexing_service: DocumentIndexingService = Depends(get_indexing_service)
):
    """
    Upload and process a PDF document.
    
    This endpoint accepts a PDF file, saves it temporarily, and starts
    background processing for parsing and indexing.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if not file.content_type or 'pdf' not in file.content_type.lower():
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed")
    
    try:
        # Generate task ID
        task_id = generate_task_id()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='upload_') as tmp_file:
            # Read and write file content
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        file_size = len(content)
        
        # Initialize task tracking
        processing_tasks[task_id] = {
            'task_id': task_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Upload completed, processing queued',
            'file_name': file.filename,
            'file_size': file_size,
            'uploaded_at': datetime.utcnow(),
            'started_at': None,
            'completed_at': None,
            'error': None,
            'result': None
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            task_id,
            tmp_file_path,
            file.filename,
            indexing_service
        )
        
        logger.info(
            "Document upload initiated",
            file_name=file.filename,
            file_size=file_size,
            task_id=task_id
        )
        
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded successfully. Processing started.",
            task_id=task_id,
            file_name=file.filename,
            file_size=file_size
        )
        
    except Exception as e:
        logger.error("Document upload failed", file_name=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/processing-status/{task_id}", response_model=DocumentProcessingStatus)
async def get_processing_status(task_id: str):
    """
    Get the processing status of a document by task ID.
    
    Returns current status, progress, and results when completed.
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = processing_tasks[task_id]
    
    return DocumentProcessingStatus(
        task_id=task_id,
        status=task_data['status'],
        progress=task_data['progress'],
        message=task_data['message'],
        file_name=task_data.get('file_name'),
        started_at=task_data.get('started_at'),
        completed_at=task_data.get('completed_at'),
        error=task_data.get('error'),
        result=task_data.get('result')
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip"),
    indexing_service: DocumentIndexingService = Depends(get_indexing_service)
):
    """
    Get a list of all indexed documents with their metadata.
    
    Returns paginated list of documents with basic metadata.
    """
    try:
        # Get document statistics and information
        stats = await indexing_service.get_document_stats()
        
        # For now, return mock data structure since the indexing service 
        # doesn't have a direct "list documents" method
        # In a real implementation, you'd query the vector store or maintain a documents table
        
        documents = []
        total = stats.get('total_documents', 0)
        
        # This is a placeholder - in production you'd have a proper documents table
        # or query the vector store for document metadata
        
        return DocumentListResponse(
            documents=documents,
            total=total
        )
        
    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/metadata/{file_name}", response_model=DocumentMetadataResponse)
async def get_document_metadata(
    file_name: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service)
):
    """
    Get detailed metadata for a specific document.
    
    Returns comprehensive metadata including topics, concepts, and processing info.
    """
    try:
        # Search for the document
        search_results = await indexing_service.search_documents(
            query=f"filename:{file_name}",
            limit=1,
            filters={'file_name': file_name}
        )
        
        if not search_results:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = search_results[0]
        metadata = doc_data.get('metadata', {})
        
        return DocumentMetadataResponse(
            file_name=file_name,
            file_path=metadata.get('file_path', ''),
            title=metadata.get('title'),
            author=metadata.get('author'),
            pages=metadata.get('total_pages', 0),
            file_size=metadata.get('file_size', 0),
            indexed_at=metadata.get('indexed_at'),
            topics=metadata.get('topics', []),
            key_concepts=metadata.get('key_concepts', []),
            total_chunks=metadata.get('total_chunks', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get document metadata", file_name=file_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")


@router.delete("/delete/{file_name}", response_model=DocumentDeletionResponse)
async def delete_document(
    file_name: str,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service)
):
    """
    Delete a document from the index.
    
    Removes the document and all its associated chunks from the vector store.
    """
    try:
        # Delete from index
        success = await indexing_service.delete_document(file_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found or deletion failed")
        
        logger.info("Document deleted successfully", file_name=file_name)
        
        return DocumentDeletionResponse(
            success=True,
            message="Document deleted successfully",
            file_name=file_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete document", file_name=file_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/extract-topics", response_model=TopicExtractionResponse)
async def extract_topics(
    request: TopicExtractionRequest,
    indexing_service: DocumentIndexingService = Depends(get_indexing_service)
):
    """
    Extract topics and key concepts from provided text.
    
    This endpoint can be used to analyze text content and extract
    relevant topics and concepts for quiz generation.
    """
    try:
        import time
        start_time = time.time()
        
        # Extract topics using the indexing service
        topics = await indexing_service._extract_topics(request.text)
        
        # For concepts, we'll use a simple approach here
        # In production, you might want to use more sophisticated NLP
        parser = DocumentParser()
        concepts = parser._extract_key_concepts(request.text)
        
        processing_time = time.time() - start_time
        
        # Limit results based on request
        topics = topics[:request.max_topics]
        concepts = concepts[:request.max_topics]
        
        logger.info(
            "Topic extraction completed",
            topics_count=len(topics),
            concepts_count=len(concepts),
            processing_time=processing_time
        )
        
        return TopicExtractionResponse(
            topics=topics,
            concepts=concepts,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error("Topic extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Topic extraction failed: {str(e)}")


@router.get("/processing-tasks")
async def list_processing_tasks():
    """
    Get a list of all processing tasks and their statuses.
    
    Useful for monitoring and debugging document processing.
    """
    return {
        "tasks": list(processing_tasks.values()),
        "total": len(processing_tasks)
    }


@router.delete("/clear-tasks")
async def clear_completed_tasks():
    """
    Clear all completed and failed processing tasks.
    
    Helps clean up the task tracking storage.
    """
    initial_count = len(processing_tasks)
    
    # Remove completed and failed tasks
    completed_tasks = [
        task_id for task_id, task_data in processing_tasks.items()
        if task_data['status'] in ['completed', 'failed']
    ]
    
    for task_id in completed_tasks:
        del processing_tasks[task_id]
    
    return {
        "message": f"Cleared {len(completed_tasks)} completed/failed tasks",
        "initial_count": initial_count,
        "remaining_count": len(processing_tasks)
    } 