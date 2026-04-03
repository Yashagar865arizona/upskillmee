from sqlalchemy.orm import Session
from sqlalchemy import text
import json

# Import base VectorStore class
from .embedding_service import VectorStore


class PGVectorStore(VectorStore):
    def __init__(self, dimension: int, db: Session):
        super().__init__(dimension)
        self.db = db

    async def init(self):
        # Ensure pgvector extension is enabled and table exists.
        # Ideally, this should be handled via a database migration.
        create_table_query = text(f"""
            CREATE TABLE IF NOT EXISTS pg_vectors (
                message_id TEXT PRIMARY KEY,
                vector vector({{self.dimension}}),
                namespace TEXT,
                metadata JSONB
            );
        """)
        self.db.execute(create_table_query)
        self.db.commit()

    async def upsert(self, vectors, namespace: str):
        for vec in vectors:
            # Use "message_id" from metadata if available or fallback to vec["id"]
            message_id = vec["metadata"].get("message_id", vec["id"])
            # Convert embedding list to a comma-separated string
            vector_str = ','.join(str(x) for x in vec["values"])
            metadata_json = json.dumps(vec["metadata"])
            query = text("""
                INSERT INTO pg_vectors (message_id, vector, namespace, metadata)
                VALUES (:message_id, :vector, :namespace, :metadata)
                ON CONFLICT (message_id)
                DO UPDATE SET
                  vector = EXCLUDED.vector,
                  metadata = EXCLUDED.metadata,
                  namespace = EXCLUDED.namespace
            """)
            self.db.execute(query, {
                "message_id": message_id,
                "vector": vector_str,
                "namespace": namespace,
                "metadata": metadata_json
            })
        self.db.commit()

    async def query(self, vector, top_k: int, namespace: str = None):
        vector_str = ','.join(str(x) for x in vector)
        if namespace:
            query = text(f"""
                SELECT message_id, metadata, vector <-> (:query_vector::vector({self.dimension})) AS distance
                FROM pg_vectors
                WHERE namespace = :namespace
                ORDER BY vector <-> (:query_vector::vector({self.dimension}))
                LIMIT :top_k
            """)
            result = self.db.execute(query, {
                "query_vector": vector_str,
                "namespace": namespace,
                "top_k": top_k
            })
        else:
            query = text(f"""
                SELECT message_id, metadata, vector <-> (:query_vector::vector({self.dimension})) AS distance
                FROM pg_vectors
                ORDER BY vector <-> (:query_vector::vector({self.dimension}))
                LIMIT :top_k
            """)
            result = self.db.execute(query, {
                "query_vector": vector_str,
                "top_k": top_k
            })

        matches = []
        for row in result:
            matches.append({
                "id": row["message_id"],
                "score": row["distance"],
                "metadata": json.loads(row["metadata"])
            })
        
        # Mimic a similar return structure as other vector stores
        class QueryResult:
            def __init__(self, matches):
                self.matches = matches
        
        return QueryResult(matches) 