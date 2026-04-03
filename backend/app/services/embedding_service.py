"""
Location: ponder/backend/app/services/embedding_service.py

This service handles vector embeddings for chat messages using OpenAI's embedding API
and vector similarity search (Qdrant locally, Pinecone in production).

Features:
- Vector embedding creation
- Similarity search
- Vector store management
- Error handling and monitoring
"""

import openai
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.chat import Message
from ..config import settings
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import time
from uuid import uuid4
from fastapi import HTTPException
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Type definitions
@dataclass
class SearchMatch:
    """Match result from vector search"""
    id: str
    score: float
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """Result from vector search"""
    matches: List[SearchMatch]

class VectorStore:
    """Abstract base class for vector stores"""
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.store = None

    async def init(self) -> None:
        """Initialize the vector store"""
        pass

    async def upsert(self, vectors: List[Dict[str, Any]], namespace: str) -> None:
        """Insert or update vectors"""
        pass

    async def query(self, vector: List[float], top_k: int, namespace: Optional[str] = None) -> SearchResult:
        """Query for similar vectors"""
        return SearchResult(matches=[])

class PineconeStore(VectorStore):
    def __init__(self, dimension: int):
        super().__init__(dimension)
        try:
            # Import Pinecone SDK
            from pinecone import Pinecone, ServerlessSpec

            # Validate API key
            if not settings.PINECONE_API_KEY:
                raise ValueError("Pinecone API key is not set. Please set PINECONE_API_KEY in your environment variables.")

            # Log API key length for debugging (don't log the actual key)
            logger.info(f"Using Pinecone API key (length: {len(settings.PINECONE_API_KEY)})")

            # Initialize Pinecone client with new API
            # Create an instance of the Pinecone class
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            # Check if index exists
            index_name = "ponder-embeddings"
            logger.info(f"Checking for existing Pinecone index: {index_name}")
            existing_indexes = self.pc.list_indexes().names()
            logger.info(f"Found existing indexes: {existing_indexes}")

            if index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {index_name}")
                # Create index with new API
                self.pc.create_index(
                    name=index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=getattr(settings, "PINECONE_REGION", "us-west-2")
                    )
                )
                logger.info(f"Successfully created Pinecone index: {index_name}")
            else:
                logger.info(f"Using existing Pinecone index: {index_name}")

            # Get the index with new API
            self.store = self.pc.Index(index_name)
            logger.info("Successfully initialized Pinecone store")
        except ImportError:
            raise ImportError("Pinecone SDK not installed. Please install with 'pip install pinecone'")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize vector store")

    async def upsert(self, vectors: List[Dict[str, Any]], namespace: str) -> None:
        """Insert or update vectors"""
        try:
            # Format vectors for new Pinecone API
            formatted_vectors = []
            for v in vectors:
                formatted_vectors.append({
                    "id": v["id"],
                    "values": v["values"],
                    "metadata": v["metadata"]
                })

            # Upsert with new API
            self.store.upsert(
                vectors=formatted_vectors,
                namespace=namespace
            )
            logger.debug(f"Successfully upserted {len(vectors)} vectors to namespace {namespace}")
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise HTTPException(status_code=500, detail="Failed to store vectors")

    async def query(self, vector: List[float], top_k: int, namespace: Optional[str] = None) -> SearchResult:
        """Query for similar vectors"""
        try:
            # Query with new API
            query_params = {
                "vector": vector,
                "top_k": top_k,
                "include_metadata": True
            }

            if namespace:
                query_params["namespace"] = namespace

            results = self.store.query(**query_params)

            # Process results with new API format
            matches = []
            for match in results.matches:
                matches.append(SearchMatch(
                    id=match.id,
                    score=float(match.score),
                    metadata=match.metadata
                ))

            return SearchResult(matches=matches)
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            raise HTTPException(status_code=500, detail="Failed to query vectors")

    async def find_similar(
        self,
        db: Session,
        query_embedding: np.ndarray,
        user_id: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar messages using vector similarity."""
        try:
            if not self.store:
                raise HTTPException(status_code=500, detail="Vector store not initialized")

            # Convert numpy array to list
            vector_list = query_embedding.tolist()
            if not isinstance(vector_list, list):
                vector_list = [float(x) for x in query_embedding.flatten()]

            results = await self.store.query(
                vector=vector_list,
                top_k=k,
                namespace=user_id
            )

            # Format results
            formatted_results = []
            for match in results.matches:
                message = db.query(Message).filter(
                    Message.id == match.metadata.get("message_id")
                ).first()

                if message is not None:
                    # Convert SQLAlchemy model attributes to Python types
                    metadata = {}
                    try:
                        metadata_value = getattr(message, 'message_metadata', None)
                        if metadata_value is not None:
                            metadata = dict(metadata_value)
                    except (TypeError, ValueError):
                        metadata = {}

                    formatted_results.append({
                        'user_id': str(message.user_id),
                        'content': str(message.content),
                        'timestamp': message.created_at,
                        'metadata': metadata,
                        'similarity_score': match.score
                    })

            return formatted_results

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding similar messages: {e}")
            raise HTTPException(status_code=500, detail="Failed to find similar messages")

class QdrantStore(VectorStore):
    def __init__(self, dimension: int):
        super().__init__(dimension)
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models

            # Try to connect to Qdrant with more detailed logging
            host = settings.QDRANT_HOST
            port = settings.QDRANT_PORT
            logger.info(f"Attempting to connect to Qdrant at {host}:{port}")

            # Add connection timeout to avoid hanging
            self.client = QdrantClient(host, port=port, timeout=5.0)
            self.models = models

            # Test connection
            try:
                collections = self.client.get_collections()
                logger.info(f"Successfully connected to Qdrant. Available collections: {collections}")
            except Exception as conn_err:
                logger.error(f"Connected to Qdrant but failed to get collections: {conn_err}")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            logger.error("Falling back to in-memory vector store")
            # Instead of failing, we'll create an in-memory fallback
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            self.client = QdrantClient(":memory:")
            self.models = models

    async def init(self) -> None:
        try:
            # Check if collection exists first
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if "ponder-embeddings" not in collection_names:
                logger.info("Creating 'ponder-embeddings' collection in Qdrant")
                self.client.create_collection(
                    collection_name="ponder-embeddings",
                    vectors_config=self.models.VectorParams(
                        size=self.dimension,
                        distance=self.models.Distance.COSINE
                    )
                )
                logger.info("Successfully created 'ponder-embeddings' collection")
            else:
                logger.info("Collection 'ponder-embeddings' already exists")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            # Don't raise exception, just log the error
            # This allows the application to continue even if vector storage fails

    async def upsert(self, vectors: List[Dict[str, Any]], namespace: str) -> None:
        try:
            points = []
            for vec in vectors:
                points.append(self.models.PointStruct(
                    id=vec["id"],
                    vector=vec["values"],
                    payload={
                        **vec["metadata"],
                        "namespace": namespace
                    }
                ))
            self.client.upsert(
                collection_name="ponder-embeddings",
                points=points
            )
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise HTTPException(status_code=500, detail="Failed to store vectors")

    async def query(self, vector: List[float], top_k: int, namespace: Optional[str] = None) -> SearchResult:
        try:
            search_params = {
                "collection_name": "ponder-embeddings",
                "query_vector": vector,
                "limit": top_k,
            }
            if namespace:
                search_params["query_filter"] = self.models.Filter(
                    must=[self.models.FieldCondition(
                        key="namespace",
                        match=self.models.MatchValue(value=namespace)
                    )]
                )

            results = self.client.search(**search_params)

            # Convert to standard format
            matches = [
                SearchMatch(
                    id=str(hit.id),
                    score=float(hit.score),
                    metadata=dict(hit.payload or {})
                ) for hit in results
            ]

            return SearchResult(matches=matches)

        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            raise HTTPException(status_code=500, detail="Failed to search vectors")

class EmbeddingService:
    """Service for creating and managing embeddings."""

    def __init__(self, db: Optional[Session] = None):
        """Initialize the embedding service."""
        self.db = db
        self.dimension = 1536  # OpenAI's ada-002 dimension
        self.store: Optional[VectorStore] = None
        self._initialized = False
        self._init_lock = None

    async def ensure_initialized(self):
        """Ensure the embedding service is properly initialized."""
        if self._initialized:
            return

        if self._init_lock is None:
            import asyncio
            self._init_lock = asyncio.Lock()

        async with self._init_lock:
            if self._initialized:
                return

            try:
                await self._initialize_vector_store()
                self._initialized = True
                logger.info("Successfully initialized EmbeddingService")
            except Exception as e:
                logger.error(f"Failed to initialize EmbeddingService: {e}")
                self._initialized = False

    async def _initialize_vector_store(self):
        """Initialize the vector store with proper error handling."""
        # Use the vector store type from settings, or fall back to a default
        vector_store_type = getattr(settings, 'VECTOR_STORE_TYPE', 'qdrant').lower()
        logger.info(f"Using vector store type: {vector_store_type}")

        if vector_store_type == 'pinecone' and settings.ENVIRONMENT == "production" and settings.PINECONE_API_KEY:
            logger.info("Initializing Pinecone vector store for production")
            self.store = PineconeStore(dimension=self.dimension)
            await self.store.init()
        else:
            # Default to Qdrant for all other cases
            logger.info(f"Using Qdrant vector store for {settings.ENVIRONMENT} environment")
            await self._initialize_qdrant_store()

    async def _initialize_qdrant_store(self):
        """Initialize Qdrant store with fallback options."""
        # Try different connection options
        connection_attempts = [
            (settings.QDRANT_HOST, settings.QDRANT_PORT),
            ("localhost", 6333),  # Default Qdrant port
            ("localhost", 8000),  # MCP port
        ]

        for host, port in connection_attempts:
            try:
                logger.info(f"Attempting to connect to Qdrant at {host}:{port}")
                # Temporarily override settings for this attempt
                original_host = settings.QDRANT_HOST
                original_port = settings.QDRANT_PORT
                settings.QDRANT_HOST = host
                settings.QDRANT_PORT = port
                
                self.store = QdrantStore(dimension=self.dimension)
                await self.store.init()
                
                logger.info(f"Successfully connected to Qdrant at {host}:{port}")
                return
                
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant at {host}:{port}: {e}")
                # Restore original settings
                settings.QDRANT_HOST = original_host
                settings.QDRANT_PORT = original_port
                continue

        # If all connection attempts fail, use in-memory Qdrant
        logger.warning("All Qdrant connection attempts failed, using in-memory store")
        self.store = QdrantStore(dimension=self.dimension)
        await self.store.init()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def create_embedding(self, text: str) -> Optional[np.ndarray]:
        """Create embedding for a text using OpenAI API."""
        try:
            start_time = time.time()

            # Create embedding
            response = openai.embeddings.create(
                input=[text],
                model="text-embedding-ada-002"
            )

            # Convert to numpy array
            embedding = np.array(response.data[0].embedding, dtype=np.float32)

            # Record metrics (simplified)
            duration = time.time() - start_time
            logger.debug(f"Embedding created in {duration:.2f}s")

            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create embedding")

    async def search_similar_conversations(
        self,
        db: Session,
        user_id: str,
        query_embedding: np.ndarray,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar conversations for a specific user."""
        try:
            if not self.store:
                raise HTTPException(status_code=500, detail="Vector store not initialized")

            # Convert numpy array to list
            vector_list = query_embedding.tolist()
            if not isinstance(vector_list, list):
                vector_list = [float(x) for x in query_embedding.flatten()]

            results = await self.store.query(
                vector=vector_list,
                top_k=limit,
                namespace=user_id
            )

            # Format results
            formatted_results = []
            for match in results.matches:
                message = db.query(Message).filter(
                    Message.id == match.metadata.get("message_id")
                ).first()

                if message is not None:
                    formatted_results.append({
                        'conversation_id': str(message.conversation_id),
                        'content': str(message.content),
                        'timestamp': message.created_at,
                        'similarity_score': match.score
                    })

            return formatted_results

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching similar conversations: {e}")
            raise HTTPException(status_code=500, detail="Failed to search conversations")

    async def store_conversation(
        self,
        db: Session,
        user_id: str,
        text: str,
        embedding: np.ndarray,
        conversation_id: int,
        role: str = 'user'
    ) -> Optional[Message]:
        """Store a conversation with its embedding."""
        # First, store the message in the database
        message = None
        try:
            # Create message using SQLAlchemy model
            message = Message()
            # Set attributes safely
            for attr, value in {
                'user_id': user_id,
                'conversation_id': conversation_id,
                'content': text,
                'role': role,
                'embedding': embedding.tobytes()
            }.items():
                setattr(message, attr, value)

            db.add(message)
            db.flush()
            logger.info(f"Successfully stored message in database with ID: {message.id}")

            # Commit the database transaction to ensure the message is saved
            # even if vector storage fails
            db.commit()

        except Exception as db_error:
            logger.error(f"Error storing message in database: {db_error}")
            if db:
                db.rollback()
            raise HTTPException(status_code=500, detail="Failed to store message in database")

        # Then, try to store in vector database (but don't fail if this part fails)
        if message and self.store:
            try:
                # Convert numpy array to list
                vector_list = embedding.tolist()
                if not isinstance(vector_list, list):
                    vector_list = [float(x) for x in embedding.flatten()]

                # Store in vector database
                await self.store.upsert(
                    vectors=[{
                        "id": str(message.id),
                        "values": vector_list,
                        "metadata": {
                            "message_id": str(message.id),
                            "conversation_id": str(conversation_id),
                            "timestamp": message.created_at.timestamp()
                        }
                    }],
                    namespace=user_id
                )
                logger.info(f"Successfully stored embedding in vector store for message ID: {message.id}")
            except Exception as vector_error:
                # Log the error but don't fail the whole operation
                logger.error(f"Error storing embedding in vector store: {vector_error}")
                logger.warning("Continuing without vector storage for this message")
                # The message is already saved in the database, so we can continue

        return message

    async def initialize_index(self):
        """Initialize the vector store."""
        if not self.store:
            logger.warning("Vector store not initialized, skipping index initialization")
            return

        try:
            await self.store.init()
            logger.info("Successfully initialized vector store index")
        except Exception as e:
            logger.error(f"Error initializing vector store index: {e}")
            logger.warning("Continuing without vector store functionality")
            # Don't raise an exception, just log the error

    async def migrate_embeddings(self, db: Session):
        """Migrate embeddings from PostgreSQL to vector store"""
        try:
            # Get all messages that have embeddings in metadata
            messages = db.query(Message).filter(
                Message.message_metadata.op('?')('embedding')  # type: ignore
            ).all()

            logger.info(f"Found {len(messages)} messages with embeddings to migrate")

            # Migrate each message's embedding
            for message in messages:
                try:
                    # Extract embedding from metadata safely
                    metadata = {}
                    try:
                        metadata_value = getattr(message, 'message_metadata', None)
                        if metadata_value is not None:
                            metadata = dict(metadata_value)
                    except (TypeError, ValueError):
                        metadata = {}

                    embedding_data = metadata.get('embedding')
                    if not embedding_data:
                        continue

                    # Convert to numpy array
                    embedding_array = np.array(embedding_data, dtype=np.float32)

                    # Convert numpy array to list
                    vector_list = embedding_array.tolist()
                    if not isinstance(vector_list, list):
                        vector_list = [float(x) for x in embedding_array.flatten()]

                    # Store in vector store
                    vector_id = str(uuid4())
                    if self.store:
                        await self.store.upsert(
                            vectors=[{
                                "id": vector_id,
                                "values": vector_list,
                                "metadata": {
                                    "message_id": str(message.id),
                                    "conversation_id": str(message.conversation_id),
                                    "role": str(message.role),
                                    "timestamp": message.created_at.isoformat()
                                }
                            }],
                            namespace=str(message.user_id)
                        )

                    # Remove embedding from metadata
                    if isinstance(metadata, dict) and 'embedding' in metadata:
                        metadata.pop('embedding', None)
                        setattr(message, 'message_metadata', metadata)

                except Exception as e:
                    logger.error(f"Error migrating message {message.id}: {str(e)}")
                    continue

            # Commit changes
            db.commit()
            logger.info("Migration completed successfully")

        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            db.rollback()

    async def store_conversation_embedding(
        self,
        db: Session,
        user_id: str,
        conversation_id: str,
        message_content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store conversation message with embedding for future retrieval."""
        try:
            await self.ensure_initialized()
            
            # Create embedding for the message
            embedding = await self.create_embedding(message_content)
            if embedding is None:
                logger.warning("Failed to create embedding for conversation message")
                return False

            # Prepare metadata
            message_metadata = {
                "conversation_id": conversation_id,
                "role": role,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                **(metadata or {})
            }

            # Store in vector database if available
            if self.store:
                try:
                    vector_list = embedding.tolist()
                    if not isinstance(vector_list, list):
                        vector_list = [float(x) for x in embedding.flatten()]

                    # Generate unique ID for this message embedding
                    from uuid import uuid4
                    embedding_id = str(uuid4())

                    await self.store.upsert(
                        vectors=[{
                            "id": embedding_id,
                            "values": vector_list,
                            "metadata": message_metadata
                        }],
                        namespace=user_id
                    )
                    
                    logger.debug(f"Stored conversation embedding for user {user_id}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to store conversation embedding: {e}")
                    return False
            else:
                logger.warning("Vector store not available for conversation embedding")
                return False

        except Exception as e:
            logger.error(f"Error storing conversation embedding: {e}")
            return False

    async def get_relevant_contexts(
        self,
        db: Session,
        user_id: str,
        query: str,
        limit: int = 5,
        exclude_conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the most relevant contexts for a query, specifically structured for chat memory.

        Args:
            db: Database session
            user_id: The user ID to search conversations for
            query: The text query to find similar messages
            limit: Maximum number of relevant contexts to return
            exclude_conversation_id: Optional conversation ID to exclude (typically the current one)

        Returns:
            List of relevant message contexts
        """
        try:
            await self.ensure_initialized()
            
            # First, create an embedding for the query
            query_embedding = await self.create_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to create embedding for context query")
                return []

            # Search for similar messages using the embedding
            similar_messages = await self.search_similar_conversations(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                limit=limit * 2  # Get more results than needed so we can filter and still have enough
            )

            if not similar_messages:
                logger.info("No similar messages found for context")
                return []

            # Filter out messages from the excluded conversation if specified
            if exclude_conversation_id:
                similar_messages = [
                    msg for msg in similar_messages
                    if str(msg.get('conversation_id', '')) != str(exclude_conversation_id)
                ]

            # Format contexts for the RAG system
            formatted_contexts = []
            for msg in similar_messages[:limit]:  # Take only up to the limit
                content = msg.get('content', '')
                similarity = msg.get('similarity_score', 0)
                timestamp = msg.get('timestamp')

                # Skip very short messages or those with low similarity
                if len(content) < 20 or similarity < 0.7:
                    continue

                # Format a nice context entry
                formatted_contexts.append({
                    'content': content,
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'similarity': round(similarity, 2),
                })

            logger.info(f"Retrieved {len(formatted_contexts)} relevant contexts using RAG")
            return formatted_contexts

        except Exception as e:
            logger.error(f"Error getting relevant contexts: {str(e)}")
            return []

    async def cleanup_old_embeddings(
        self,
        user_id: Optional[str] = None,
        days_old: int = 90,
        keep_important: bool = True
    ) -> Dict[str, int]:
        """Clean up old embeddings to manage vector database storage."""
        try:
            await self.ensure_initialized()
            
            if not self.store:
                logger.warning("Vector store not available for cleanup")
                return {"deleted": 0, "kept": 0}

            # For now, we'll implement a simple cleanup strategy
            # In a production system, you'd want more sophisticated cleanup logic
            
            cutoff_timestamp = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # This is a simplified cleanup - in practice, you'd need to:
            # 1. Query the vector store for old embeddings
            # 2. Evaluate which ones to keep based on importance
            # 3. Delete the ones that should be removed
            
            logger.info(f"Embedding cleanup completed for embeddings older than {days_old} days")
            
            # Return placeholder stats - implement actual cleanup logic based on your vector store
            return {
                "deleted": 0,
                "kept": 0,
                "message": "Cleanup logic needs to be implemented for specific vector store"
            }
            
        except Exception as e:
            logger.error(f"Error during embedding cleanup: {e}")
            return {"error": str(e)}