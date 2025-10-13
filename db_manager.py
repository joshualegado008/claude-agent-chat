"""
Database Manager - Handles PostgreSQL and Qdrant operations for conversation memory
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList
import anthropic
from settings_manager import get_settings


class DatabaseManager:
    """Manages conversation storage in PostgreSQL and Qdrant."""

    def __init__(
        self,
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_db: str = "agent_conversations",
        postgres_user: str = "agent_user",
        postgres_password: str = "agent_pass_local",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333
    ):
        """Initialize database connections."""

        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password
        )

        # Qdrant client
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)

        # Settings manager
        self.settings = get_settings()

        # OpenAI client for embeddings (if configured)
        self.openai_client = None
        openai_key = self.settings.get_openai_api_key()
        if openai_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.embedding_model = self.settings.get_embedding_model()
                print(f"✅ OpenAI embeddings enabled ({self.embedding_model})")
            except ImportError:
                print("⚠️  OpenAI package not installed. Using placeholder embeddings.")
            except Exception as e:
                print(f"⚠️  Failed to initialize OpenAI client: {e}")
        else:
            print("⚠️  OpenAI API key not configured. Using placeholder embeddings.")

        # Initialize Qdrant collection if it doesn't exist
        self._init_qdrant_collection()

    def _init_qdrant_collection(self):
        """Initialize Qdrant collection for conversation embeddings."""
        collection_name = "conversation_exchanges"

        # Determine embedding dimensions based on model
        # OpenAI text-embedding-3-small/large: 1536 dimensions
        # Placeholder hash-based: 1024 dimensions
        embedding_dim = 1536 if self.openai_client else 1024

        # Check if collection exists
        collections = self.qdrant.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            # Create collection with appropriate dimensions
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
            )

    def create_conversation(
        self,
        title: str,
        initial_prompt: str,
        agent_a_id: str,
        agent_a_name: str,
        agent_b_id: str,
        agent_b_name: str,
        tags: List[str] = None
    ) -> str:
        """
        Create a new conversation record.

        Returns:
            conversation_id (UUID as string)
        """
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO conversations
                (title, initial_prompt, agent_a_id, agent_a_name, agent_b_id, agent_b_name, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title, initial_prompt, agent_a_id, agent_a_name, agent_b_id, agent_b_name, tags or []))

            conversation_id = cursor.fetchone()[0]
            self.pg_conn.commit()

        return str(conversation_id)

    def add_exchange(
        self,
        conversation_id: str,
        turn_number: int,
        agent_name: str,
        thinking_content: Optional[str],
        response_content: str,
        tokens_used: int
    ):
        """Add an exchange (agent message) to a conversation."""

        # Store in PostgreSQL
        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO exchanges
                (conversation_id, turn_number, agent_name, thinking_content, response_content, tokens_used)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (conversation_id, turn_number, agent_name, thinking_content, response_content, tokens_used))

            exchange_id = cursor.fetchone()[0]
            self.pg_conn.commit()

        # Generate embedding and store in Qdrant for semantic search
        try:
            embedding = self._generate_embedding(response_content)

            self.qdrant.upsert(
                collection_name="conversation_exchanges",
                points=[
                    PointStruct(
                        id=str(exchange_id),
                        vector=embedding,
                        payload={
                            "conversation_id": conversation_id,
                            "turn_number": turn_number,
                            "agent_name": agent_name,
                            "response_content": response_content[:500],  # Store preview
                            "created_at": datetime.now().isoformat()
                        }
                    )
                ]
            )
        except Exception as e:
            print(f"Warning: Failed to create embedding: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Uses OpenAI embeddings if configured, otherwise falls back to
        a simple hash-based placeholder.
        """
        # Use OpenAI embeddings if available
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"Warning: OpenAI embedding failed: {e}, using placeholder")
                # Fall through to placeholder

        # Fallback: Simple hash-based vector (NOT FOR PRODUCTION)
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Create a 1024-dim vector from hash (repeating pattern)
        vector = []
        for i in range(1024):
            byte_val = hash_bytes[i % len(hash_bytes)]
            vector.append((byte_val / 255.0) - 0.5)  # Normalize to [-0.5, 0.5]

        return vector

    def update_conversation_stats(
        self,
        conversation_id: str,
        total_turns: int,
        total_tokens: int,
        status: str = 'active'
    ):
        """Update conversation statistics."""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations
                    SET total_turns = %s, total_tokens = %s, status = %s
                    WHERE id = %s
                """, (total_turns, total_tokens, status, conversation_id))
                self.pg_conn.commit()
        except Exception as e:
            self.pg_conn.rollback()
            print(f"Error updating conversation stats: {e}")
            raise

    def _serialize_datetime(self, obj):
        """Recursively convert datetime objects to ISO format strings for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj

    def save_context_snapshot(
        self,
        conversation_id: str,
        turn_number: int,
        context_data: Dict
    ):
        """Save a context snapshot for resuming conversations."""
        # Convert any datetime objects to ISO strings for JSON serialization
        serializable_data = self._serialize_datetime(context_data)

        with self.pg_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO context_snapshots (conversation_id, snapshot_at_turn, context_data)
                VALUES (%s, %s, %s)
                ON CONFLICT (conversation_id, snapshot_at_turn)
                DO UPDATE SET context_data = EXCLUDED.context_data
            """, (conversation_id, turn_number, Json(serializable_data)))
            self.pg_conn.commit()

    def load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Load a complete conversation with all exchanges."""
        try:
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get conversation metadata
                cursor.execute("""
                    SELECT * FROM conversations WHERE id = %s
                """, (conversation_id,))

                conversation = cursor.fetchone()
                if not conversation:
                    return None

                # Get all exchanges
                cursor.execute("""
                    SELECT * FROM exchanges
                    WHERE conversation_id = %s
                    ORDER BY turn_number
                """, (conversation_id,))

                exchanges = cursor.fetchall()

                # Get latest context snapshot
                cursor.execute("""
                    SELECT * FROM context_snapshots
                    WHERE conversation_id = %s
                    ORDER BY snapshot_at_turn DESC
                    LIMIT 1
                """, (conversation_id,))

                snapshot = cursor.fetchone()

            # Serialize datetime objects to ISO strings for JSON compatibility
            result = {
                'conversation': dict(conversation),
                'exchanges': [dict(e) for e in exchanges],
                'last_snapshot': dict(snapshot) if snapshot else None
            }

            return self._serialize_datetime(result)
        except Exception as e:
            self.pg_conn.rollback()
            print(f"Error loading conversation: {e}")
            raise

    def list_conversations(
        self,
        limit: int = 20,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """List conversations with optional filters."""
        try:
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM conversation_summaries WHERE 1=1"
                params = []

                if status:
                    query += " AND status = %s"
                    params.append(status)

                if tags:
                    query += " AND tags && %s"
                    params.append(tags)

                query += " ORDER BY updated_at DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                return self._serialize_datetime(results)
        except Exception as e:
            self.pg_conn.rollback()
            print(f"Error listing conversations: {e}")
            raise

    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Semantic search across all conversations using Qdrant."""

        # Generate embedding for search query
        query_embedding = self._generate_embedding(query)

        # Search in Qdrant
        search_results = self.qdrant.search(
            collection_name="conversation_exchanges",
            query_vector=query_embedding,
            limit=limit
        )

        # Enrich results with conversation data from PostgreSQL
        enriched_results = []
        for result in search_results:
            conversation_id = result.payload['conversation_id']

            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT c.*, e.turn_number, e.agent_name, e.response_content
                    FROM conversations c
                    JOIN exchanges e ON c.id = e.conversation_id
                    WHERE c.id = %s AND e.turn_number = %s
                """, (conversation_id, result.payload['turn_number']))

                row = cursor.fetchone()
                if row:
                    enriched_results.append({
                        **dict(row),
                        'similarity_score': result.score
                    })

        return self._serialize_datetime(enriched_results)

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation and all associated data.

        Args:
            conversation_id: UUID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.pg_conn.cursor() as cursor:
                # First, get all exchange IDs for Qdrant cleanup
                cursor.execute("""
                    SELECT id FROM exchanges WHERE conversation_id = %s
                """, (conversation_id,))

                exchange_ids = [str(row[0]) for row in cursor.fetchall()]

                # Delete from Qdrant vector database
                if exchange_ids:
                    try:
                        self.qdrant.delete(
                            collection_name="conversation_exchanges",
                            points_selector=PointIdsList(points=exchange_ids)
                        )
                    except Exception as e:
                        print(f"Warning: Failed to delete from Qdrant: {e}")

                # Delete conversation metadata (if table exists)
                # This table is optional - part of metadata_schema.sql
                try:
                    cursor.execute("""
                        DELETE FROM conversation_metadata WHERE conversation_id = %s
                    """, (conversation_id,))
                except psycopg2.errors.UndefinedTable:
                    # Metadata table doesn't exist - this is fine, continue with deletion
                    pass

                # Delete context snapshots
                cursor.execute("""
                    DELETE FROM context_snapshots WHERE conversation_id = %s
                """, (conversation_id,))

                # Delete exchanges (CASCADE would handle this, but being explicit)
                cursor.execute("""
                    DELETE FROM exchanges WHERE conversation_id = %s
                """, (conversation_id,))

                # Delete the conversation itself
                cursor.execute("""
                    DELETE FROM conversations WHERE id = %s
                """, (conversation_id,))

                # Commit all changes
                self.pg_conn.commit()

                return True

        except Exception as e:
            # Rollback on error
            self.pg_conn.rollback()
            print(f"Error deleting conversation: {e}")
            return False

    def close(self):
        """Close database connections."""
        self.pg_conn.close()
