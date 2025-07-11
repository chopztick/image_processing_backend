"""
Vector service for pgvector operations and similarity search.
Cloud-native implementation with async support and proper error handling.
"""

import asyncio
import logging
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, TimeoutError
from pgvector.sqlalchemy import Vector

from app.models.image import Image
from app.schemas.image import SimilarImage
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service for vector operations using pgvector.
    """
    
    @staticmethod
    async def find_similar_images(
        session: AsyncSession,
        query_embedding: List[float],
        query_image_id: Optional[UUID] = None,
        limit: int = 5,
        threshold: float = None,
    ) -> List[SimilarImage]:
        """
        Find similar images using pgvector cosine similarity.
        
        Args:
            session: Database session
            query_embedding: Query embedding vector
            query_image_id: ID of the query image (to exclude from results)
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of similar images with similarity scores
        """
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD
        
        try:
            logger.info(f"Starting similarity search for query_image_id={query_image_id}, threshold={threshold}, limit={limit}")
            
            # Use efficient single-query approach with SQLAlchemy ORM
            # Calculate similarity score and apply threshold in a single query
            stmt = (
                select(
                    Image.id,
                    Image.filename,
                    Image.content_type,
                    Image.upload_timestamp,
                    (1 - Image.embedding_vector.cosine_distance(query_embedding)).label('similarity_score')
                )
                .where(Image.processing_status == "completed")
                .where((1 - Image.embedding_vector.cosine_distance(query_embedding)) >= threshold)
            )
            
            # Exclude the query image if specified
            if query_image_id:
                stmt = stmt.where(Image.id != query_image_id)
            
            # Order by similarity score descending and limit results
            stmt = stmt.order_by(desc('similarity_score')).limit(limit)
            
            # Execute query with timeout for cloud-native resilience
            result = await asyncio.wait_for(
                session.execute(stmt),
                timeout=settings.DATABASE_QUERY_TIMEOUT if hasattr(settings, 'DATABASE_QUERY_TIMEOUT') else 30
            )
            rows = result.fetchall()
            
            # Convert to SimilarImage objects
            similar_images = []
            for row in rows:
                similar_images.append(SimilarImage(
                    id=row.id,
                    filename=row.filename,
                    content_type=row.content_type,
                    similarity_score=float(row.similarity_score),
                    upload_timestamp=row.upload_timestamp,
                ))
            
            logger.info(f"Similarity search completed. Found {len(similar_images)} similar images")
            return similar_images
            
        except asyncio.TimeoutError:
            logger.error(f"Similarity search timed out for query_image_id={query_image_id}")
            raise RuntimeError("Similarity search timed out - database overloaded")
        except SQLAlchemyError as e:
            logger.error(f"Database error during similarity search: {str(e)}")
            raise RuntimeError(f"Database error during similarity search: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during similarity search: {str(e)}")
            raise RuntimeError(f"Unexpected error during similarity search: {str(e)}")
    
    @staticmethod
    async def store_image_embedding(
        session: AsyncSession,
        image_id: UUID,
        embedding: List[float],
    ) -> bool:
        """
        Store or update an image's embedding vector.
        
        Args:
            session: Database session
            image_id: ID of the image
            embedding: Embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the image
            stmt = select(Image).where(Image.id == image_id)
            result = await session.execute(stmt)
            image = result.scalar_one_or_none()
            
            if not image:
                return False
            
            # Update the embedding
            image.embedding_vector = embedding
            image.processing_status = "completed"
            image.processed_timestamp = datetime.utcnow()
            
            await session.commit()
            return True
            
        except SQLAlchemyError as e:
            await session.rollback()
            raise RuntimeError(f"Database error storing embedding: {str(e)}")
    
    @staticmethod
    async def get_image_embedding(
        session: AsyncSession,
        image_id: UUID,
    ) -> Optional[List[float]]:
        """
        Get an image's embedding vector.
        
        Args:
            session: Database session
            image_id: ID of the image
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            # Use SQLAlchemy ORM to get the embedding
            stmt = select(Image.embedding_vector).where(
                and_(
                    Image.id == image_id,
                    Image.processing_status == "completed"
                )
            )
            result = await session.execute(stmt)
            embedding = result.scalar_one_or_none()
            
            # The embedding should be returned as a list directly by pgvector
            # If it's not, convert it to a list
            if embedding is not None:
                if isinstance(embedding, list):
                    return embedding
                else:
                    # Convert to list if it's not already
                    return list(embedding)
            
            return None
            
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving embedding: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error retrieving embedding: {str(e)}")
    
    @staticmethod
    async def get_embedding_stats(
        session: AsyncSession,
    ) -> dict:
        """
        Get statistics about stored embeddings.
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with embedding statistics
        """
        try:
            # Count total images
            total_count = await session.execute(
                text("SELECT COUNT(*) FROM images")
            )
            total_images = total_count.scalar()
            
            # Count processed images
            processed_count = await session.execute(
                text("SELECT COUNT(*) FROM images WHERE processing_status = 'completed'")
            )
            processed_images = processed_count.scalar()
            
            # Count pending images
            pending_count = await session.execute(
                text("SELECT COUNT(*) FROM images WHERE processing_status = 'pending'")
            )
            pending_images = pending_count.scalar()
            
            return {
                "total_images": total_images,
                "processed_images": processed_images,
                "pending_images": pending_images,
                "embedding_dimension": settings.EMBEDDING_DIMENSION,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            }
            
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving stats: {str(e)}")
    
    @staticmethod
    async def batch_similarity_search(
        session: AsyncSession,
        query_embeddings: List[List[float]],
        limit: int = 5,
        threshold: float = None,
    ) -> List[List[SimilarImage]]:
        """
        Perform batch similarity search for multiple embeddings.
        
        Args:
            session: Database session
            query_embeddings: List of query embedding vectors
            limit: Maximum number of results per query
            threshold: Similarity threshold
            
        Returns:
            List of similar images for each query
        """
        results = []
        
        for embedding in query_embeddings:
            similar_images = await VectorService.find_similar_images(
                session=session,
                query_embedding=embedding,
                limit=limit,
                threshold=threshold,
            )
            results.append(similar_images)
        
        return results
    
    @staticmethod
    async def find_duplicate_images(
        session: AsyncSession,
        threshold: float = 0.95,
        limit: int = 100,
    ) -> List[Tuple[UUID, UUID, float]]:
        """
        Find potential duplicate images based on high similarity.
        
        Args:
            session: Database session
            threshold: Similarity threshold for duplicates
            limit: Maximum number of duplicate pairs to return
            
        Returns:
            List of (image1_id, image2_id, similarity_score) tuples
        """
        try:
            # Use a more efficient approach with raw SQL for duplicate detection
            duplicate_query = text("""
                WITH image_pairs AS (
                    SELECT 
                        i1.id as id1,
                        i2.id as id2,
                        1 - (i1.embedding_vector <=> i2.embedding_vector) as similarity
                    FROM images i1
                    CROSS JOIN images i2
                    WHERE i1.processing_status = 'completed'
                        AND i2.processing_status = 'completed'
                        AND i1.id < i2.id  -- Avoid duplicates and self-comparison
                        AND (1 - (i1.embedding_vector <=> i2.embedding_vector)) >= :threshold
                )
                SELECT id1, id2, similarity
                FROM image_pairs
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            
            result = await session.execute(
                duplicate_query,
                {"threshold": threshold, "limit": limit}
            )
            rows = result.fetchall()
            
            duplicates = []
            for row in rows:
                duplicates.append((row.id1, row.id2, float(row.similarity)))
            
            return duplicates
            
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error finding duplicates: {str(e)}")