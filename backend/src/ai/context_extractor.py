"""Context extraction module for the AI-Enhanced Interactive Book Agent.

This module extracts relevant context from book content to provide to AI models
for tasks like explanation, summarization, and question answering.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import logging
from backend.src.models.sqlalchemy_models import BookContent


@dataclass
class ContextFragment:
    """Represents a fragment of extracted context."""
    content: str
    start_position: int
    end_position: int
    relevance_score: float
    metadata: Dict[str, Any]


class ContextExtractor:
    """Service for extracting relevant context from book content."""

    def __init__(self):
        """Initialize the context extractor."""
        self.logger = logging.getLogger(__name__)

    async def extract_context_for_explanation(
        self,
        target_content: str,
        book_content_chunks: List[BookContent],
        window_size: int = 2
    ) -> List[ContextFragment]:
        """Extract context for explaining specific content.

        Args:
            target_content: The content that needs explanation
            book_content_chunks: List of book content chunks to search in
            window_size: Number of chunks before and after to include as context

        Returns:
            List of context fragments relevant for explanation
        """
        try:
            # Find the chunk that contains the target content
            target_chunk_idx = -1
            for idx, chunk in enumerate(book_content_chunks):
                if target_content in chunk.content or self._is_similar_content(target_content, chunk.content):
                    target_chunk_idx = idx
                    break

            if target_chunk_idx == -1:
                # If we can't find the exact content, find the most relevant chunk
                target_chunk_idx = self._find_most_relevant_chunk_idx(target_content, book_content_chunks)

            # Extract context window around the target chunk
            context_fragments = []
            start_idx = max(0, target_chunk_idx - window_size)
            end_idx = min(len(book_content_chunks), target_chunk_idx + window_size + 1)

            for i in range(start_idx, end_idx):
                chunk = book_content_chunks[i]
                relevance_score = self._calculate_relevance_score(target_content, chunk.content)
                
                fragment = ContextFragment(
                    content=chunk.content,
                    start_position=chunk.page_number or 0,
                    end_position=chunk.page_number or 0,
                    relevance_score=relevance_score,
                    metadata={
                        "chunk_id": chunk.chunk_id,
                        "section_title": chunk.section_title,
                        "chapter": chunk.chapter,
                        "is_target_context": i == target_chunk_idx
                    }
                )
                context_fragments.append(fragment)

            # Sort by relevance score
            context_fragments.sort(key=lambda x: x.relevance_score, reverse=True)

            return context_fragments

        except Exception as e:
            self.logger.error(f"Error extracting context for explanation: {str(e)}")
            return []

    async def extract_context_for_summarization(
        self,
        book_content_chunks: List[BookContent],
        target_section: Optional[str] = None
    ) -> List[ContextFragment]:
        """Extract context for summarization tasks.

        Args:
            book_content_chunks: List of book content chunks to process
            target_section: Optional specific section to summarize

        Returns:
            List of context fragments relevant for summarization
        """
        try:
            context_fragments = []

            for chunk in book_content_chunks:
                # If target section is specified, only include chunks from that section
                if target_section and chunk.section_title != target_section:
                    continue

                relevance_score = self._calculate_summarization_relevance_score(chunk.content)

                fragment = ContextFragment(
                    content=chunk.content,
                    start_position=chunk.page_number or 0,
                    end_position=chunk.page_number or 0,
                    relevance_score=relevance_score,
                    metadata={
                        "chunk_id": chunk.chunk_id,
                        "section_title": chunk.section_title,
                        "chapter": chunk.chapter,
                        "is_important": self._is_important_section(chunk.section_title)
                    }
                )
                context_fragments.append(fragment)

            # Sort by relevance score
            context_fragments.sort(key=lambda x: x.relevance_score, reverse=True)

            return context_fragments

        except Exception as e:
            self.logger.error(f"Error extracting context for summarization: {str(e)}")
            return []

    async def extract_context_for_question(
        self,
        question: str,
        book_content_chunks: List[BookContent],
        max_fragments: int = 5
    ) -> List[ContextFragment]:
        """Extract context relevant to answering a specific question.

        Args:
            question: The question to answer
            book_content_chunks: List of book content chunks to search in
            max_fragments: Maximum number of context fragments to return

        Returns:
            List of context fragments relevant for answering the question
        """
        try:
            question_keywords = self._extract_keywords(question)

            scored_fragments = []
            for chunk in book_content_chunks:
                relevance_score = self._calculate_question_relevance_score(question, chunk.content, question_keywords)

                # Only include fragments with sufficient relevance
                if relevance_score > 0.1:  # Threshold for relevance
                    fragment = ContextFragment(
                        content=chunk.content,
                        start_position=chunk.page_number or 0,
                        end_position=chunk.page_number or 0,
                        relevance_score=relevance_score,
                        metadata={
                            "chunk_id": chunk.chunk_id,
                            "section_title": chunk.section_title,
                            "chapter": chunk.chapter,
                            "keyword_matches": self._count_keyword_matches(question_keywords, chunk.content)
                        }
                    )
                    scored_fragments.append((fragment, relevance_score))

            # Sort by relevance score and return top max_fragments
            scored_fragments.sort(key=lambda x: x[1], reverse=True)

            # Extract just the fragments and return them
            result_fragments = [fragment for fragment, score in scored_fragments[:max_fragments]]

            return result_fragments

        except Exception as e:
            self.logger.error(f"Error extracting context for question: {str(e)}")
            return []

    async def extract_context_with_metadata(
        self,
        query: str,
        book_content_chunks: List[BookContent],
        include_metadata: List[str] = None
    ) -> List[ContextFragment]:
        """Extract context with specific metadata fields.

        Args:
            query: The query to match against
            book_content_chunks: List of book content chunks to search in
            include_metadata: List of metadata fields to include

        Returns:
            List of context fragments with specified metadata
        """
        if include_metadata is None:
            include_metadata = ["chunk_id", "section_title", "chapter", "page_number"]

        try:
            context_fragments = []

            for chunk in book_content_chunks:
                relevance_score = self._calculate_relevance_score(query, chunk.content)

                # Only include fragments with sufficient relevance
                if relevance_score > 0.05:  # Lower threshold for metadata extraction
                    metadata = {}
                    for field in include_metadata:
                        if field == "chunk_id":
                            metadata[field] = chunk.chunk_id
                        elif field == "section_title":
                            metadata[field] = chunk.section_title
                        elif field == "chapter":
                            metadata[field] = chunk.chapter
                        elif field == "page_number":
                            metadata[field] = chunk.page_number
                        elif field == "embedding_id":
                            metadata[field] = chunk.embedding_id

                    fragment = ContextFragment(
                        content=chunk.content,
                        start_position=chunk.page_number or 0,
                        end_position=chunk.page_number or 0,
                        relevance_score=relevance_score,
                        metadata=metadata
                    )
                    context_fragments.append(fragment)

            # Sort by relevance score
            context_fragments.sort(key=lambda x: x.relevance_score, reverse=True)

            return context_fragments

        except Exception as e:
            self.logger.error(f"Error extracting context with metadata: {str(e)}")
            return []

    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """Calculate a relevance score between query and content.

        Args:
            query: The query string
            content: The content string

        Returns:
            Relevance score between 0 and 1
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # Calculate keyword overlap
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(content_words))
        jaccard_similarity = overlap / len(query_words.union(content_words)) if query_words.union(content_words) else 0.0

        # Calculate phrase matches (boost for consecutive word matches)
        phrase_score = 0
        query_words_list = list(query_words)
        if len(query_words_list) > 1:
            for i in range(len(query_words_list) - 1):
                phrase = query_words_list[i] + " " + query_words_list[i + 1]
                if phrase in content_lower:
                    phrase_score += 0.1

        # Combine scores
        total_score = jaccard_similarity + phrase_score
        return min(1.0, total_score)  # Cap at 1.0

    def _calculate_summarization_relevance_score(self, content: str) -> float:
        """Calculate relevance score for summarization.

        Args:
            content: The content string

        Returns:
            Relevance score between 0 and 1
        """
        # Longer content fragments are more likely to be relevant for summarization
        length_score = min(1.0, len(content) / 1000)  # Normalize based on expected content length

        # Check for important keywords that suggest informative content
        important_keywords = [
            "important", "key", "main", "summary", "conclusion", 
            "significant", "crucial", "notable", "essential"
        ]
        keyword_score = sum(1 for keyword in important_keywords if keyword in content.lower())
        keyword_score = min(0.5, keyword_score * 0.1)  # Cap keyword score

        return (length_score * 0.7) + (keyword_score * 0.3)

    def _calculate_question_relevance_score(
        self,
        question: str,
        content: str,
        question_keywords: List[str]
    ) -> float:
        """Calculate relevance score for question answering.

        Args:
            question: The question
            content: The content to score
            question_keywords: Keywords extracted from the question

        Returns:
            Relevance score between 0 and 1
        """
        content_lower = content.lower()

        # Count keyword matches
        keyword_matches = sum(1 for keyword in question_keywords if keyword.lower() in content_lower)
        keyword_score = keyword_matches / len(question_keywords) if question_keywords else 0.0

        # Calculate semantic similarity using simple word overlap
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        semantic_score = len(question_words.intersection(content_words)) / len(question_words) if question_words else 0.0

        # Combine scores
        return (keyword_score * 0.6) + (semantic_score * 0.4)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Simple keyword extraction using regex
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords

    def _count_keyword_matches(self, keywords: List[str], text: str) -> int:
        """Count how many keywords match in the text.

        Args:
            keywords: List of keywords to search for
            text: Text to search in

        Returns:
            Number of keyword matches
        """
        text_lower = text.lower()
        return sum(1 for keyword in keywords if keyword.lower() in text_lower)

    def _is_similar_content(self, content1: str, content2: str, threshold: float = 0.7) -> bool:
        """Check if two content strings are similar.

        Args:
            content1: First content string
            content2: Second content string
            threshold: Similarity threshold (0-1)

        Returns:
            True if contents are similar, False otherwise
        """
        # Simple similarity check based on word overlap
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))

        if not words1 and not words2:
            return True
        if not words1 or not words2:
            return False

        similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        return similarity >= threshold

    def _find_most_relevant_chunk_idx(self, target_content: str, chunks: List[BookContent]) -> int:
        """Find the most relevant chunk index for target content.

        Args:
            target_content: Target content to match against
            chunks: List of content chunks

        Returns:
            Index of the most relevant chunk
        """
        best_score = -1
        best_idx = 0

        for idx, chunk in enumerate(chunks):
            score = self._calculate_relevance_score(target_content, chunk.content)
            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def _is_important_section(self, section_title: str) -> bool:
        """Determine if a section title indicates an important section.

        Args:
            section_title: Title of the section

        Returns:
            True if the section is likely important, False otherwise
        """
        if not section_title:
            return False

        important_indicators = [
            "introduction", "summary", "conclusion", "overview", 
            "key points", "important", "essential", "critical"
        ]

        section_lower = section_title.lower()
        return any(indicator in section_lower for indicator in important_indicators)


# Global instance of the context extractor
context_extractor = ContextExtractor()