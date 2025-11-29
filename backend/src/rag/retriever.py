"""Ranked retrieval system for the AI-Enhanced Interactive Book Agent.

This module implements ranked retrieval of relevant sections from documents
using semantic similarity and other ranking algorithms.
"""
from typing import List, Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod
import numpy as np
from scipy.spatial.distance import cosine
from backend.src.rag.vector_store import vector_store
from backend.src.rag.embedding_generator import embedding_generator
from backend.src.models.sqlalchemy_models import BookContent


class BaseRetriever(ABC):
    """Base class for different retrieval strategies."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of top results to return
            **kwargs: Additional parameters for specific retrieval strategies

        Returns:
            List of retrieved document dictionaries
        """
        pass


class SemanticRetriever(BaseRetriever):
    """Retriever that uses semantic similarity for ranking."""

    def __init__(self):
        """Initialize the semantic retriever."""
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator

    async def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using semantic similarity.

        Args:
            query: The search query
            top_k: Number of top results to return
            **kwargs: Additional parameters

        Returns:
            List of retrieved document dictionaries with similarity scores
        """
        # Generate embedding for the query
        query_embedding = await self.embedding_generator.generate_embedding(query)
        if not query_embedding:
            return []

        # Get all documents from the vector store
        # In a real implementation, you might want to filter by book ID or other criteria
        results = await self.vector_store.search(query, n_results=top_k)

        # Sort by distance (smaller distance = more similar)
        results.sort(key=lambda x: x['distance'])

        # Format the results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['id'],
                'content': result['content'],
                'metadata': result['metadata'],
                'similarity_score': 1.0 - result['distance'],  # Convert distance to similarity
                'rank': len(formatted_results) + 1  # Simple rank based on position
            })

        return formatted_results


class BM25Retriever(BaseRetriever):
    """Retriever implementing BM25 algorithm for keyword-based ranking."""

    def __init__(self):
        """Initialize the BM25 retriever."""
        # BM25 parameters
        self.k1 = 1.2  # BM25 term frequency saturation parameter
        self.b = 0.75  # BM25 length normalization parameter

    async def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using BM25 algorithm.

        Args:
            query: The search query
            top_k: Number of top results to return
            **kwargs: Additional parameters

        Returns:
            List of retrieved document dictionaries with BM25 scores
        """
        # In a real implementation, this would connect to a search engine like Elasticsearch
        # or implement the full BM25 algorithm using document term frequencies
        # For now, we'll simulate the results by using the vector store search
        # and then calculating a simple term-based score
        results = await vector_store.search(query, n_results=top_k)

        # Calculate a simple term-based score (this is a simplified approximation)
        query_words = set(query.lower().split())
        formatted_results = []
        for result in results:
            content_words = set(result['content'].lower().split())
            overlap = len(query_words.intersection(content_words))
            score = overlap / len(query_words) if len(query_words) > 0 else 0

            formatted_results.append({
                'id': result['id'],
                'content': result['content'],
                'metadata': result['metadata'],
                'bm25_score': score,
                'rank': len(formatted_results) + 1
            })

        return formatted_results


class HybridRetriever(BaseRetriever):
    """Retriever that combines semantic and keyword-based approaches."""

    def __init__(self, semantic_weight: float = 0.7, keyword_weight: float = 0.3):
        """Initialize the hybrid retriever.

        Args:
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
        """
        self.semantic_retriever = SemanticRetriever()
        self.keyword_retriever = BM25Retriever()
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    async def retrieve(self, query: str, top_k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve documents using a combination of semantic and keyword approaches.

        Args:
            query: The search query
            top_k: Number of top results to return
            **kwargs: Additional parameters

        Returns:
            List of retrieved document dictionaries with combined scores
        """
        # Get results from both retrievers
        semantic_results = await self.semantic_retriever.retrieve(query, top_k * 2)
        keyword_results = await self.keyword_retriever.retrieve(query, top_k * 2)

        # Create a map of document IDs to their scores
        result_scores = {}

        # Add semantic scores
        for result in semantic_results:
            doc_id = result['id']
            if doc_id not in result_scores:
                result_scores[doc_id] = {'document': result, 'semantic_score': 0, 'keyword_score': 0}
            result_scores[doc_id]['semantic_score'] = result.get('similarity_score', 0)

        # Add keyword scores
        for result in keyword_results:
            doc_id = result['id']
            if doc_id not in result_scores:
                result_scores[doc_id] = {'document': result, 'semantic_score': 0, 'keyword_score': 0}
            result_scores[doc_id]['keyword_score'] = result.get('bm25_score', 0)

        # Calculate combined scores
        combined_results = []
        for doc_id, scores in result_scores.items():
            combined_score = (
                self.semantic_weight * scores['semantic_score'] +
                self.keyword_weight * scores['keyword_score']
            )

            # Use the document data from the semantic retriever as the base
            result = scores['document'].copy()
            result['combined_score'] = combined_score
            result['semantic_score'] = scores['semantic_score']
            result['keyword_score'] = scores['keyword_score']

            combined_results.append(result)

        # Sort by combined score
        combined_results.sort(key=lambda x: x['combined_score'], reverse=True)

        # Return top_k results
        return combined_results[:top_k]


class RankedRetrievalService:
    """Service for ranked retrieval of relevant sections."""

    def __init__(self):
        """Initialize the ranked retrieval service with different retrieval strategies."""
        self.semantic_retriever = SemanticRetriever()
        self.keyword_retriever = BM25Retriever()
        self.hybrid_retriever = HybridRetriever()

    async def retrieve_by_semantic_similarity(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using semantic similarity.

        Args:
            query: The search query
            book_id: Optional book ID to filter results
            top_k: Number of top results to return

        Returns:
            List of retrieved document dictionaries
        """
        # If book_id is specified, we would need to modify the vector store to allow filtering
        # For now, we'll just retrieve using the standard method
        results = await self.semantic_retriever.retrieve(query, top_k)

        # Filter by book_id if specified
        if book_id:
            results = [
                result for result in results
                if result.get('metadata', {}).get('book_id') == book_id
            ]

        return results

    async def retrieve_by_keyword_matching(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using keyword matching.

        Args:
            query: The search query
            book_id: Optional book ID to filter results
            top_k: Number of top results to return

        Returns:
            List of retrieved document dictionaries
        """
        results = await self.keyword_retriever.retrieve(query, top_k)

        # Filter by book_id if specified
        if book_id:
            results = [
                result for result in results
                if result.get('metadata', {}).get('book_id') == book_id
            ]

        return results

    async def retrieve_hybrid(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using a hybrid approach combining semantic and keyword matching.

        Args:
            query: The search query
            book_id: Optional book ID to filter results
            top_k: Number of top results to return

        Returns:
            List of retrieved document dictionaries
        """
        results = await self.hybrid_retriever.retrieve(query, top_k)

        # Filter by book_id if specified
        if book_id:
            results = [
                result for result in results
                if result.get('metadata', {}).get('book_id') == book_id
            ]

        return results

    async def retrieve_with_reranking(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve documents and apply reranking for improved relevance.

        Args:
            query: The search query
            book_id: Optional book ID to filter results
            top_k: Number of top results to return

        Returns:
            List of retrieved and reranked document dictionaries
        """
        # Get more results than needed for reranking purposes
        initial_results = await self.hybrid_retriever.retrieve(query, top_k * 2)

        # Filter by book_id if specified
        if book_id:
            initial_results = [
                result for result in initial_results
                if result.get('metadata', {}).get('book_id') == book_id
            ]

        # Apply reranking - in a real implementation, this might use cross-encoder models
        # or other re-ranking algorithms
        reranked_results = self._rerank_results(query, initial_results)

        return reranked_results[:top_k]

    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply reranking to improve the relevance of results.

        Args:
            query: The original search query
            results: List of initial results

        Returns:
            List of reranked results
        """
        # In a real implementation, this would use sophisticated re-ranking models
        # For now, we'll apply a simple re-ranking based on multiple factors:
        # 1. Semantic similarity
        # 2. Term overlap
        # 3. Content length (preferably not too short or too long)
        # 4. Position in document (earlier sections might be more relevant for some queries)

        query_words = set(query.lower().split())
        reranked_with_scores = []

        for result in results:
            content = result['content']
            content_words = content.lower().split()

            # Calculate term overlap
            term_overlap = len(query_words.intersection(set(content_words))) / len(query_words) if query_words else 0

            # Calculate content length score (penalize very short or very long snippets)
            length_score = 1.0  # Start with base score
            if len(content_words) < 20 or len(content_words) > 500:  # Adjust these thresholds as needed
                length_score = 0.5

            # Calculate position score (earlier sections might be more relevant)
            # This would be based on metadata about the document structure
            position_score = 1.0  # Default

            # Combined score
            combined_score = (
                0.5 * result.get('combined_score', result.get('semantic_score', 0)) +
                0.3 * term_overlap +
                0.1 * length_score +
                0.1 * position_score
            )

            reranked_item = result.copy()
            reranked_item['reranked_score'] = combined_score
            reranked_with_scores.append(reranked_item)

        # Sort by reranked score
        reranked_with_scores.sort(key=lambda x: x['reranked_score'], reverse=True)

        return reranked_with_scores


# Global instance of the retrieval service
retrieval_service = RankedRetrievalService()