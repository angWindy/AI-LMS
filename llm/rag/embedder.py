"""Embedding service for RAG system using Gemini models."""

import logging
from typing import Optional
import numpy as np

try:
    from google import genai
except ImportError:
    genai = None

from llm.rag.chunker import Chunk, Document
from llm.config import LLMConfig


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using Google Gemini models."""
    
    # Available Gemini embedding models {model_name: output_dimension}
    MODELS = {
        'gemini-embedding-001': 3072,  # latest model, highest quality
        'text-embedding-004': 768,     # older model, lower dim
    }
    
    def __init__(
        self,
        model: str = 'gemini-embedding-001',
        api_key: Optional[str] = None,
        verbose: bool = True,
    ):
        """Initialize embedding service.
        
        Args:
            model: Embedding model to use
            api_key: Google API key
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {list(self.MODELS.keys())}")
        
        self.model = model
        self.embedding_dimension = self.MODELS[model]
        
        # Initialize Gemini client
        if api_key is None:
            config = LLMConfig.from_env()
            api_key = config.google_api_key
        
        if not api_key:
            raise ValueError("Google API key not found. Set GOOGLE_AI_API_KEY environment variable.")
        
        if genai is None:
            raise ImportError("google-genai package not installed. Install it with: pip install google-genai")

        self.client = genai.Client(api_key=api_key)
        
        if self.verbose:
            logger.info(f"[Embedding] Initialized service with model: {model}")
            logger.info(f"[Embedding] Embedding dimension: {self.embedding_dimension}")
    
    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not text.strip():
            logger.warning("[Embedding] Empty text provided for embedding")
            return [0.0] * self.embedding_dimension
        
        try:
            if self.verbose:
                logger.debug(f"[Embedding] Generating embedding for text ({len(text)} chars)")
            
            response = self._embed_content(text, task_type)
            embedding = self._extract_embedding(response)
            
            if self.verbose:
                logger.debug(f"[Embedding] Generated embedding with dimension: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"[Embedding] Error generating embedding: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimension
    
    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            if self.verbose:
                logger.debug(f"[Embedding] Generating query embedding: {query[:100]}...")
            
            response = self._embed_content(query, "RETRIEVAL_QUERY")
            embedding = self._extract_embedding(response)
            
            if self.verbose:
                logger.debug(f"[Embedding] Query embedding generated with dimension: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"[Embedding] Error generating query embedding: {str(e)}")
            return [0.0] * self.embedding_dimension
    
    def embed_chunks(self, chunks: list[Chunk], task_type: str = "RETRIEVAL_DOCUMENT") -> list[Chunk]:
        """Generate embeddings for multiple chunks.
        
        Args:
            chunks: List of chunks to embed
            task_type: Task type for embedding (RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY)
            
        Returns:
            List of chunks with embeddings
        """
        if self.verbose:
            logger.info(f"[Embedding] Starting to embed {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, 1):
            if self.verbose and i % 10 == 0:
                logger.info(f"[Embedding] Progress: {i}/{len(chunks)} chunks")
            if chunk.metadata.get("is_structural"):
                continue
            chunk.embedding = self.embed_text(chunk.content, task_type=task_type)
        
        if self.verbose:
            logger.info(f"[Embedding] Completed embedding {len(chunks)} chunks")
        
        return chunks
    
    def embed_document(self, document: Document) -> Document:
        """Generate embeddings for all chunks in a document.
        
        Args:
            document: Document object
            
        Returns:
            Document with embedded chunks
        """
        if self.verbose:
            logger.info(f"[Embedding] Embedding document: {document.title}")
            logger.info(f"[Embedding] Total chunks to embed: {len(document.chunks)}")
        
        self.embed_chunks(document.chunks)
        
        if self.verbose:
            logger.info(f"[Embedding] Document embedding completed")
        
        return document
    
    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        # Handle zero vectors
        if np.linalg.norm(arr1) == 0 or np.linalg.norm(arr2) == 0:
            return 0.0
        
        similarity = np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2))
        return float(max(0.0, similarity))  # Ensure non-negative
    
    def find_similar_chunks(
        self,
        query_embedding: list[float],
        chunks: list[Chunk],
        top_k: int = 5,
    ) -> list[tuple[Chunk, float]]:
        """Find most similar chunks for a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            chunks: List of chunks to search
            top_k: Number of top results to return
            
        Returns:
            List of (chunk, similarity_score) tuples sorted by similarity
        """
        if self.verbose:
            logger.debug(f"[Embedding] Searching for {top_k} similar chunks from {len(chunks)} total")
        
        similarities = []
        for chunk in chunks:
            if chunk.embedding:
                sim = self.cosine_similarity(query_embedding, chunk.embedding)
                similarities.append((chunk, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        result = similarities[:top_k]
        
        if self.verbose:
            logger.debug(f"[Embedding] Found {len(result)} similar chunks")
            for chunk, sim in result[:3]:
                logger.debug(f"[Embedding] - {chunk.id}: similarity={sim:.4f}")
        
        return result

    def _embed_content(self, text: str, task_type: str) -> object:
        """Call the Gemini embedding API, handling SDK version differences."""
        try:
            # google-genai >= 1.x: task_type passed via config dict
            return self.client.models.embed_content(
                model=f"models/{self.model}",
                contents=text,
                config={"task_type": task_type},
            )
        except Exception:
            # Fallback: omit config (works without task_type too)
            return self.client.models.embed_content(
                model=f"models/{self.model}",
                contents=text,
            )

    def _extract_embedding(self, response: object) -> list[float]:
        """Extract float vector from various Gemini response shapes."""
        # google-genai >= 1.x: response.embeddings is a list of ContentEmbedding
        embeddings_attr = getattr(response, "embeddings", None)
        if isinstance(embeddings_attr, list) and embeddings_attr:
            first = embeddings_attr[0]
            if hasattr(first, "values") and first.values:
                return list(first.values)

        # Older SDK: response.embedding with .values
        embedding_attr = getattr(response, "embedding", None)
        if embedding_attr is not None:
            if hasattr(embedding_attr, "values"):
                return list(embedding_attr.values)
            if isinstance(embedding_attr, (list, tuple)):
                return list(embedding_attr)

        # Dict-style response
        if isinstance(response, dict):
            for key in ("embeddings", "embedding"):
                val = response.get(key)
                if val:
                    if hasattr(val, "values"):
                        return list(val.values)
                    if isinstance(val, list) and val:
                        if hasattr(val[0], "values"):
                            return list(val[0].values)
                        return list(val)

        raise ValueError(f"Unrecognised embedding response shape: {type(response)}")
