"""
Document Management Service for RAG (Retrieval Augmented Generation)

This service handles:
- Loading documents from filesystem
- Splitting documents into passages
- Searching for relevant passages based on user queries
- Using passages as context for OpenAI responses
"""

import os
import re
from pathlib import Path
import logging
from django.conf import settings
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class DocumentManager:
    """Manage document storage and retrieval"""
    
    def __init__(self):
        self.docs_folder = os.path.join(
            settings.BASE_DIR,
            'knowledge_base'
        )
        # Create folder if it doesn't exist
        os.makedirs(self.docs_folder, exist_ok=True)
        logger.info(f"Document folder: {self.docs_folder}")
    
    def load_document_from_file(self, file_path: str) -> Tuple[str, str]:
        """Load document content and title from file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get title from filename
            title = Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
            
            return title, content
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            raise
    
    def save_document_to_file(self, filename: str, content: str) -> str:
        """Save document content to file"""
        try:
            file_path = os.path.join(self.docs_folder, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Document saved: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the knowledge base folder"""
        try:
            documents = []
            for filename in os.listdir(self.docs_folder):
                if filename.endswith(('.txt', '.md', '.pdf')):
                    file_path = os.path.join(self.docs_folder, filename)
                    file_size = os.path.getsize(file_path)
                    
                    documents.append({
                        'filename': filename,
                        'path': file_path,
                        'size': file_size,
                        'type': Path(filename).suffix[1:]
                    })
            
            return sorted(documents, key=lambda x: x['filename'])
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    @staticmethod
    def split_document_into_passages(content: str, passage_length: int = 300) -> List[str]:
        """
        Split document into passages for better retrieval
        
        Args:
            content: Full document content
            passage_length: Approximate number of words per passage
        
        Returns:
            List of passages
        """
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        passages = []
        current_passage = []
        current_length = 0
        
        for paragraph in paragraphs:
            words = len(paragraph.split())
            
            if current_length + words > passage_length and current_passage:
                # Save current passage and start new one
                passages.append('\n\n'.join(current_passage).strip())
                current_passage = [paragraph]
                current_length = words
            else:
                current_passage.append(paragraph)
                current_length += words
        
        # Add remaining passage
        if current_passage:
            passages.append('\n\n'.join(current_passage).strip())
        
        return [p for p in passages if p.strip()]
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 5) -> List[str]:
        """Extract keywords from text"""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'are', 'be', 'been', 'being', 'have', 'has', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter and count
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in keywords[:num_keywords]]


class DocumentRetriever:
    """Retrieve relevant documents/passages based on queries"""
    
    @staticmethod
    def calculate_text_similarity(query: str, text: str) -> float:
        """
        Calculate similarity between query and text using simple metrics
        
        Returns similarity score 0-1
        """
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        # Jaccard similarity
        if not (query_words | text_words):
            return 0.0
        
        intersection = len(query_words & text_words)
        union = len(query_words | text_words)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def search_passages(query: str, passages: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Search for most relevant passages given a query
        
        Args:
            query: User's question/query
            passages: List of document passages
            top_k: Number of top results to return
        
        Returns:
            List of (passage, similarity_score) tuples
        """
        scored_passages = []
        
        for passage in passages:
            similarity = DocumentRetriever.calculate_text_similarity(query, passage)
            if similarity > 0:  # Only include passages with some match
                scored_passages.append((passage, similarity))
        
        # Sort by similarity score
        scored_passages.sort(key=lambda x: x[1], reverse=True)
        
        return scored_passages[:top_k]
    
    @staticmethod
    def find_relevant_passages_in_db(query: str, limit: int = 5) -> List['DocumentPassage']:
        """
        Find relevant passages from database based on query
        
        Uses simple keyword and text similarity matching
        """
        from recommendations.models import DocumentPassage
        
        try:
            # Get all active passages
            all_passages = DocumentPassage.objects.filter(is_active=True)
            
            # Score each passage
            scored = []
            for passage in all_passages:
                # Keyword matching
                query_words = set(query.lower().split())
                passage_keywords = set(passage.keywords)
                keyword_matches = len(query_words & passage_keywords)
                
                # Text similarity  
                text_sim = DocumentRetriever.calculate_text_similarity(
                    query, 
                    passage.passage_text
                )
                
                # Combined score (weight keyword matches + text similarity)
                score = (keyword_matches * 0.3) + (text_sim * 100)
                
                if score > 0:
                    scored.append((passage, score))
            
            # Sort and return top results
            scored.sort(key=lambda x: x[1], reverse=True)
            return [p[0] for p in scored[:limit]]
            
        except Exception as e:
            logger.error(f"Error finding passages: {e}")
            return []


# Singleton instances
document_manager = DocumentManager()
document_retriever = DocumentRetriever()
