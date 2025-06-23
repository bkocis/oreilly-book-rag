"""
Vector Store Service

This service provides advanced vector database operations for document storage and retrieval,
including similarity search, metadata filtering, batch processing, and topic-based clustering.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import json
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    Range, MatchValue, SearchRequest, ScrollRequest, UpdateResult
)
from sentence_transformers import SentenceTransformer
import structlog

logger = structlog.get_logger(__name__)


class VectorStoreService:
    """Advanced vector store service for document storage and retrieval."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "oreilly_documents",
        embedding_model: str = "BAAI/bge-small-en-v1.5"
    ):
        """Initialize the vector store service."""
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            host=self.qdrant_host,
            port=self.qdrant_port
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Setup collection
        self._setup_collection()
        
        logger.info(
            "Vector store service initialized",
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            embedding_model=embedding_model,
            embedding_dimension=self.embedding_dimension
        )
    
    def _setup_collection(self):
        """Setup Qdrant collection with proper configuration."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection with optimized settings
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    "Created Qdrant collection",
                    collection_name=self.collection_name,
                    dimension=self.embedding_dimension
                )
            else:
                logger.info(
                    "Using existing Qdrant collection",
                    collection_name=self.collection_name
                )
                
        except Exception as e:
            logger.error(
                "Failed to setup collection",
                error=str(e),
                collection_name=self.collection_name
            )
            raise
    
    async def store_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Store multiple documents in the vector database with batch processing.
        
        Args:
            documents: List of documents with 'text' and 'metadata' fields
            batch_size: Number of documents to process in each batch
            
        Returns:
            Dictionary with storage results
        """
        try:
            logger.info(
                "Starting batch document storage",
                total_documents=len(documents),
                batch_size=batch_size
            )
            
            stored_count = 0
            failed_count = 0
            batches_processed = 0
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                try:
                    # Prepare batch for storage
                    points = []
                    texts = [doc['text'] for doc in batch]
                    
                    # Generate embeddings for batch
                    embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
                    
                    # Create points for Qdrant
                    for j, (doc, embedding) in enumerate(zip(batch, embeddings)):
                        point_id = f"{datetime.utcnow().timestamp()}_{i + j}"
                        
                        # Ensure metadata has required fields
                        metadata = doc.get('metadata', {})
                        metadata.update({
                            'stored_at': datetime.utcnow().isoformat(),
                            'text_length': len(doc['text']),
                            'embedding_model': self.embedding_model_name
                        })
                        
                        point = PointStruct(
                            id=point_id,
                            vector=embedding.tolist(),
                            payload=metadata
                        )
                        points.append(point)
                    
                    # Store batch in Qdrant
                    result = self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    
                    stored_count += len(batch)
                    batches_processed += 1
                    
                    logger.info(
                        "Batch stored successfully",
                        batch_number=batches_processed,
                        batch_size=len(batch),
                        total_stored=stored_count
                    )
                    
                except Exception as batch_error:
                    logger.error(
                        "Failed to store batch",
                        batch_number=batches_processed + 1,
                        error=str(batch_error)
                    )
                    failed_count += len(batch)
            
            result = {
                'success': True,
                'total_documents': len(documents),
                'stored_count': stored_count,
                'failed_count': failed_count,
                'batches_processed': batches_processed,
                'storage_time': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Batch document storage completed",
                **result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to store documents",
                error=str(e),
                total_documents=len(documents)
            )
            raise
    
    async def similarity_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search with optional metadata filtering.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores and metadata
        """
        try:
            logger.info(
                "Performing similarity search",
                query_length=len(query),
                limit=limit,
                score_threshold=score_threshold,
                has_filters=filters is not None
            )
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Build Qdrant filter if provided
            qdrant_filter = None
            if filters:
                qdrant_filter = self._build_qdrant_filter(filters)
            
            # Perform search
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for point in search_result:
                result = {
                    'id': point.id,
                    'score': point.score,
                    'metadata': point.payload,
                    'text': point.payload.get('text', ''),
                }
                results.append(result)
            
            logger.info(
                "Similarity search completed",
                results_found=len(results),
                query_length=len(query)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Failed to perform similarity search",
                error=str(e),
                query_length=len(query)
            )
            raise
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from metadata filters."""
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, dict):
                # Handle range filters
                if 'gte' in value or 'lte' in value or 'gt' in value or 'lt' in value:
                    range_condition = Range()
                    if 'gte' in value:
                        range_condition.gte = value['gte']
                    if 'lte' in value:
                        range_condition.lte = value['lte']
                    if 'gt' in value:
                        range_condition.gt = value['gt']
                    if 'lt' in value:
                        range_condition.lt = value['lt']
                    
                    conditions.append(
                        FieldCondition(key=field, range=range_condition)
                    )
            elif isinstance(value, list):
                # Handle multiple values (OR condition)
                for v in value:
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=v))
                    )
            else:
                # Handle exact match
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
        
        return Filter(must=conditions) if conditions else None
    
    async def cluster_by_topics(
        self,
        filters: Optional[Dict[str, Any]] = None,
        min_cluster_size: int = 5
    ) -> Dict[str, Any]:
        """
        Perform topic-based clustering of documents.
        
        Args:
            filters: Optional metadata filters to apply before clustering
            min_cluster_size: Minimum number of documents per cluster
            
        Returns:
            Dictionary with clustering results
        """
        try:
            logger.info(
                "Starting topic-based clustering",
                min_cluster_size=min_cluster_size,
                has_filters=filters is not None
            )
            
            # Build filter
            qdrant_filter = None
            if filters:
                qdrant_filter = self._build_qdrant_filter(filters)
            
            # Scroll through all documents
            documents = []
            offset = None
            
            while True:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=qdrant_filter,
                    limit=1000,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                if not scroll_result[0]:  # No more documents
                    break
                
                documents.extend(scroll_result[0])
                offset = scroll_result[1]  # Next offset
            
            if len(documents) < min_cluster_size:
                return {
                    'success': False,
                    'message': f'Not enough documents for clustering. Found {len(documents)}, need at least {min_cluster_size}',
                    'document_count': len(documents)
                }
            
            # Extract topics from metadata
            topic_clusters = defaultdict(list)
            
            for doc in documents:
                metadata = doc.payload
                
                # Try to get topics from various metadata fields
                topics = []
                if 'topics' in metadata:
                    topics.extend(metadata['topics'] if isinstance(metadata['topics'], list) else [metadata['topics']])
                if 'categories' in metadata:
                    topics.extend(metadata['categories'] if isinstance(metadata['categories'], list) else [metadata['categories']])
                if 'subject' in metadata:
                    topics.append(metadata['subject'])
                
                # If no topics found, try to extract from filename or content type
                if not topics:
                    if 'file_name' in metadata:
                        # Simple topic extraction from filename
                        filename = metadata['file_name'].lower()
                        if 'python' in filename:
                            topics.append('python')
                        elif 'machine' in filename and 'learning' in filename:
                            topics.append('machine_learning')
                        elif 'data' in filename:
                            topics.append('data_science')
                        else:
                            topics.append('general')
                    else:
                        topics.append('uncategorized')
                
                # Add document to relevant topic clusters
                for topic in topics:
                    topic_clusters[topic].append({
                        'id': doc.id,
                        'metadata': metadata,
                        'vector': doc.vector
                    })
            
            # Filter clusters by minimum size
            valid_clusters = {
                topic: docs for topic, docs in topic_clusters.items()
                if len(docs) >= min_cluster_size
            }
            
            # Calculate cluster statistics
            cluster_stats = {}
            for topic, docs in valid_clusters.items():
                # Calculate centroid
                vectors = np.array([doc['vector'] for doc in docs])
                centroid = np.mean(vectors, axis=0)
                
                # Calculate intra-cluster similarity
                similarities = []
                for i, vec1 in enumerate(vectors):
                    for vec2 in vectors[i+1:]:
                        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                        similarities.append(similarity)
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                
                cluster_stats[topic] = {
                    'document_count': len(docs),
                    'centroid': centroid.tolist(),
                    'average_similarity': float(avg_similarity),
                    'documents': [
                        {
                            'id': doc['id'],
                            'file_name': doc['metadata'].get('file_name', 'unknown'),
                            'content_type': doc['metadata'].get('content_type', 'unknown')
                        }
                        for doc in docs
                    ]
                }
            
            result = {
                'success': True,
                'total_documents': len(documents),
                'total_clusters': len(valid_clusters),
                'min_cluster_size': min_cluster_size,
                'clusters': cluster_stats,
                'clustered_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Topic-based clustering completed",
                total_documents=len(documents),
                total_clusters=len(valid_clusters),
                largest_cluster=max([stats['document_count'] for stats in cluster_stats.values()]) if cluster_stats else 0
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to perform topic-based clustering",
                error=str(e)
            )
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection."""
        try:
            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            # Count documents
            count_result = self.qdrant_client.count(
                collection_name=self.collection_name
            )
            
            # Get sample documents for metadata analysis
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True
            )
            
            # Analyze metadata
            metadata_analysis = self._analyze_metadata([doc.payload for doc in scroll_result[0]])
            
            stats = {
                'collection_name': self.collection_name,
                'document_count': count_result.count,
                'vector_dimension': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.name,
                'metadata_fields': metadata_analysis,
                'status': collection_info.status.name,
                'indexed_vectors_count': collection_info.vectors_count,
                'points_count': collection_info.points_count
            }
            
            logger.info(
                "Collection statistics retrieved",
                document_count=stats['document_count'],
                vector_dimension=stats['vector_dimension']
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to get collection statistics",
                error=str(e)
            )
            raise
    
    def _analyze_metadata(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze metadata fields and their distributions."""
        if not metadata_list:
            return {}
        
        field_analysis = {}
        
        # Count field occurrences and analyze types
        for metadata in metadata_list:
            for field, value in metadata.items():
                if field not in field_analysis:
                    field_analysis[field] = {
                        'count': 0,
                        'types': Counter(),
                        'sample_values': []
                    }
                
                field_analysis[field]['count'] += 1
                field_analysis[field]['types'][type(value).__name__] += 1
                
                # Store sample values (limit to 5)
                if len(field_analysis[field]['sample_values']) < 5:
                    field_analysis[field]['sample_values'].append(str(value)[:100])
        
        # Convert Counter objects to regular dicts for JSON serialization
        for field in field_analysis:
            field_analysis[field]['types'] = dict(field_analysis[field]['types'])
        
        return field_analysis
    
    async def delete_documents(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delete documents matching the given filters.
        
        Args:
            filters: Metadata filters to select documents for deletion
            
        Returns:
            Dictionary with deletion results
        """
        try:
            logger.info(
                "Starting document deletion",
                filters=filters
            )
            
            # Build Qdrant filter
            qdrant_filter = self._build_qdrant_filter(filters)
            
            # First, count how many documents match
            count_result = self.qdrant_client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_filter
            )
            
            if count_result.count == 0:
                return {
                    'success': True,
                    'deleted_count': 0,
                    'message': 'No documents found matching the filters'
                }
            
            # Delete documents
            delete_result = self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_filter
            )
            
            result = {
                'success': True,
                'deleted_count': count_result.count,
                'operation_id': delete_result.operation_id if hasattr(delete_result, 'operation_id') else None,
                'deleted_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Document deletion completed",
                deleted_count=result['deleted_count']
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to delete documents",
                error=str(e),
                filters=filters
            )
            raise
    
    async def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the collection."""
        try:
            logger.info("Clearing all documents from collection")
            
            # Get count before deletion
            count_result = self.qdrant_client.count(
                collection_name=self.collection_name
            )
            
            # Delete collection and recreate
            self.qdrant_client.delete_collection(self.collection_name)
            self._setup_collection()
            
            result = {
                'success': True,
                'cleared_count': count_result.count,
                'cleared_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Collection cleared successfully",
                cleared_count=result['cleared_count']
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to clear collection",
                error=str(e)
            )
            raise


# Global instance
_vector_store_service = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create global vector store service instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service 