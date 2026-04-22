import time
import math
import chromadb
from chromadb.utils import embedding_functions
from app.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        # Using local persistence for simple multi-tenant namespaces
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )

    def get_collection(self, user_id: str):
        collection_name = f"user_{user_id.replace('@', '_').replace('.', '_')}"
        return self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    async def store(self, user_id: str, text: str, metadata: dict = None):
        collection = self.get_collection(user_id)
        doc_key = metadata.get("key", "") if metadata else ""
        metadata["active"] = metadata.get("active", True)
        
        # Conflict detection: Check if we have this key but a different value
        if doc_key:
            existing = collection.get(where={"key": doc_key})
            if existing and existing["documents"]:
                for i, ex_doc in enumerate(existing["documents"]):
                    ex_meta = existing["metadatas"][i]
                    if ex_meta.get("value") != metadata.get("value"):
                        ex_confidence = float(ex_meta.get("confidence", 0.0))
                        new_confidence = float(metadata.get("confidence", 0.0))
                        
                        ex_id = existing["ids"][i]
                        
                        # Rule 3: Both high confidence
                        if ex_confidence > 0.85 and new_confidence > 0.85:
                            # Keep both, determine active by priority
                            ex_priority = ex_confidence * float(ex_meta.get("importance_score", 0.5))
                            new_priority = new_confidence * float(metadata.get("importance_score", 0.5))
                            
                            if new_priority >= ex_priority:
                                metadata["active"] = True
                                ex_meta["active"] = False
                            else:
                                metadata["active"] = False
                                ex_meta["active"] = True
                            
                            metadata["conflict_group"] = doc_key
                            ex_meta["conflict_group"] = doc_key
                            collection.update(ids=[ex_id], metadatas=[ex_meta])
                            
                        else:
                            # Rule 1 & 2: Higher confidence or newer wins.
                            if new_confidence > ex_confidence:
                                metadata["active"] = True
                                ex_meta["active"] = False
                            elif new_confidence < ex_confidence:
                                metadata["active"] = False
                                ex_meta["active"] = True
                            else:
                                # Equal confidence. Newest wins. We are the newest.
                                metadata["active"] = True
                                ex_meta["active"] = False
                                
                            collection.update(ids=[ex_id], metadatas=[ex_meta])

        doc_id = str(uuid.uuid4())
        collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id

    async def search(self, user_id: str, query: str, limit: int = 5):
        collection = self.get_collection(user_id)
        if collection.count() == 0:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=min(limit * 3, collection.count()),
            include=["documents", "metadatas", "distances"],
            where={"active": True}  # ONLY ACTIVE MEMORIES
        )
        
        memories = []
        if not results['documents'] or not results['documents'][0]:
            return memories
            
        current_time = time.time()
        
        for i in range(len(results['documents'][0])):
            distance = results['distances'][0][i]
            similarity = max(0.0, min(1.0, 1.0 - distance))
            
            meta = results['metadatas'][0][i]
            text = results['documents'][0][i]
            
            importance = float(meta.get("importance_score", 0.5))
            confidence = float(meta.get("confidence", 0.5))
            recency_ts = float(meta.get("recency_timestamp", current_time))
            
            age_seconds = max(0, current_time - recency_ts)
            age_days = age_seconds / (86400)
            recency_boost = math.exp(-0.1 * age_days) # Decay
            
            # Updated ranking formula
            final_score = (0.35 * similarity) + (0.25 * importance) + (0.20 * recency_boost) + (0.20 * confidence)
            
            # Prune strictly anything under 0.55
            if final_score >= 0.55:
                memories.append({
                    "text": text,
                    "metadata": meta,
                    "normalized_rule": meta.get("normalized_rule", text),
                    "confidence": confidence,
                    "similarity": similarity,
                    "final_score": final_score
                })
            
        memories = sorted(memories, key=lambda x: x["final_score"], reverse=True)
        return memories[:limit]

    async def clear(self, user_id: str):
        collection_name = f"user_{user_id.replace('@', '_').replace('.', '_')}"
        try:
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            logger.error(f"Error clearing collection for {user_id}: {e}")
            return False

    def get_stats(self, user_id: str):
        collection = self.get_collection(user_id)
        return {
            "count": collection.count()
        }

vector_store = VectorStore()

