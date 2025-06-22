"""
Document Indexing Service

This service handles document indexing using LlamaIndex with Qdrant vector store.
It processes parsed documents and creates searchable embeddings.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import structlog

from ..services.document_parser import DocumentParser

logger = structlog.get_logger(__name__)


class DocumentIndexingService:
    """Service for indexing documents with LlamaIndex and Qdrant."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "oreilly_documents",
        embedding_model: str = "BAAI/bge-small-en-v1.5"
    ):
        """Initialize the indexing service."""
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            host=self.qdrant_host,
            port=self.qdrant_port
        )
        
        # Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.embedding_model,
            max_length=512
        )
        
        # Configure LlamaIndex settings
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize document parser
        self.document_parser = DocumentParser()
        
        # Initialize vector store and index
        self._setup_vector_store()
        
        logger.info(
            "Document indexing service initialized",
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
    
    def _setup_vector_store(self):
        """Setup Qdrant vector store and collection."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # BGE small embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    "Created Qdrant collection",
                    collection_name=self.collection_name
                )
            
            # Initialize vector store
            self.vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=self.collection_name
            )
            
            # Initialize index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store
            )
            
        except Exception as e:
            logger.error(
                "Failed to setup vector store",
                error=str(e),
                collection_name=self.collection_name
            )
            raise
    
    async def index_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index a single document.
        
        Args:
            file_path: Path to the document file
            metadata: Additional metadata for the document
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info("Starting document indexing", file_path=file_path)
            
            # Parse document
            parsed_doc = await self.document_parser.parse_document(file_path)
            
            if not parsed_doc or not parsed_doc.get('content'):
                raise ValueError("Document parsing failed or returned empty content")
            
            # Prepare document metadata
            doc_metadata = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'indexed_at': datetime.utcnow().isoformat(),
                'total_pages': parsed_doc.get('total_pages', 0),
                'file_size': parsed_doc.get('file_size', 0),
                **(metadata or {})
            }
            
            # Create LlamaIndex documents
            documents = []
            
            # Add full document
            full_doc = Document(
                text=parsed_doc['content'],
                metadata={
                    **doc_metadata,
                    'content_type': 'full_document',
                    'page_range': f"1-{parsed_doc.get('total_pages', 'unknown')}"
                }
            )
            documents.append(full_doc)
            
            # Add page-level documents if available
            if 'pages' in parsed_doc:
                for page_num, page_content in parsed_doc['pages'].items():
                    if page_content.strip():
                        page_doc = Document(
                            text=page_content,
                            metadata={
                                **doc_metadata,
                                'content_type': 'page',
                                'page_number': int(page_num),
                                'page_range': str(page_num)
                            }
                        )
                        documents.append(page_doc)
            
            # Index documents
            for doc in documents:
                self.index.insert(doc)
            
            # Extract topics and concepts
            topics = await self._extract_topics(parsed_doc['content'])
            
            result = {
                'success': True,
                'file_path': file_path,
                'documents_indexed': len(documents),
                'total_pages': parsed_doc.get('total_pages', 0),
                'content_length': len(parsed_doc['content']),
                'topics': topics,
                'indexed_at': doc_metadata['indexed_at']
            }
            
            logger.info(
                "Document indexing completed",
                file_path=file_path,
                documents_indexed=len(documents),
                topics_count=len(topics)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Document indexing failed",
                file_path=file_path,
                error=str(e)
            )
            return {
                'success': False,
                'file_path': file_path,
                'error': str(e)
            }
    
    async def batch_index_documents(
        self,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Index multiple documents in batch.
        
        Args:
            file_paths: List of document file paths
            metadata: Common metadata for all documents
            
        Returns:
            Dictionary with batch indexing results
        """
        logger.info("Starting batch document indexing", count=len(file_paths))
        
        results = []
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            try:
                result = await self.index_document(file_path, metadata)
                results.append(result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(
                    "Batch indexing error",
                    file_path=file_path,
                    error=str(e)
                )
                results.append({
                    'success': False,
                    'file_path': file_path,
                    'error': str(e)
                })
                failed += 1
        
        batch_result = {
            'total_files': len(file_paths),
            'successful': successful,
            'failed': failed,
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Batch document indexing completed",
            total=len(file_paths),
            successful=successful,
            failed=failed
        )
        
        return batch_result
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search indexed documents.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional filters for search
            
        Returns:
            List of search results
        """
        try:
            logger.info("Searching documents", query=query, limit=limit)
            
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=limit,
                response_mode="no_text"  # We just want the source nodes
            )
            
            # Execute search
            response = query_engine.query(query)
            
            # Process results
            results = []
            for node in response.source_nodes:
                result = {
                    'content': node.node.text,
                    'metadata': node.node.metadata,
                    'score': node.score,
                    'file_path': node.node.metadata.get('file_path', ''),
                    'file_name': node.node.metadata.get('file_name', ''),
                    'page_number': node.node.metadata.get('page_number'),
                    'content_type': node.node.metadata.get('content_type', 'unknown')
                }
                results.append(result)
            
            logger.info(
                "Document search completed",
                query=query,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Document search failed",
                query=query,
                error=str(e)
            )
            return []
    
    async def _extract_topics(self, content: str) -> List[str]:
        """
        Extract topics and key concepts from content.
        
        Args:
            content: Document content
            
        Returns:
            List of extracted topics
        """
        try:
            # Simple keyword extraction for now
            # In a production system, you might use more sophisticated NLP
            import re
            
            # Common technical terms and patterns
            patterns = [
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Title case phrases
                r'\b\w+(?:ing|tion|sion|ment|ness|ity|able|ible)\b',  # Common suffixes
                r'\b(?:API|SDK|HTTP|REST|JSON|XML|SQL|NoSQL|DevOps|CI/CD)\b',  # Tech acronyms
            ]
            
            topics = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                topics.update(match.lower() for match in matches[:20])  # Limit topics
            
            # Filter out common words
            stop_words = {
                'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
                'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
                'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
                'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
            }
            
            filtered_topics = [
                topic for topic in topics 
                if len(topic) > 3 and topic not in stop_words
            ]
            
            return sorted(filtered_topics)[:10]  # Return top 10 topics
            
        except Exception as e:
            logger.error("Topic extraction failed", error=str(e))
            return []
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed documents.
        
        Returns:
            Dictionary with document statistics
        """
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            stats = {
                'total_documents': collection_info.vectors_count,
                'collection_name': self.collection_name,
                'embedding_model': self.embedding_model,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.value
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get document stats", error=str(e))
            return {}
    
    async def delete_document(self, file_path: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            file_path: Path of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Search for documents with the given file path
            points = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "file_path",
                            "match": {"value": file_path}
                        }
                    ]
                },
                limit=1000  # Adjust as needed
            )
            
            if points[0]:  # If documents found
                point_ids = [point.id for point in points[0]]
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector={"points": point_ids}
                )
                
                logger.info(
                    "Document deleted from index",
                    file_path=file_path,
                    deleted_count=len(point_ids)
                )
                return True
            else:
                logger.warning(
                    "Document not found in index",
                    file_path=file_path
                )
                return False
                
        except Exception as e:
            logger.error(
                "Failed to delete document",
                file_path=file_path,
                error=str(e)
            )
            return False
    
    async def clear_index(self) -> bool:
        """
        Clear all documents from the index.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            self._setup_vector_store()  # Recreate collection
            
            logger.info("Index cleared successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to clear index", error=str(e))
            return False


# Singleton instance
_indexing_service = None


def get_indexing_service() -> DocumentIndexingService:
    """Get the singleton indexing service instance."""
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = DocumentIndexingService()
    return _indexing_service 