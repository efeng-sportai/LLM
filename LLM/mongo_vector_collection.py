from typing import List, Dict, Optional, Any, Union
import uuid
import numpy as np
from pymongo.mongo_client import MongoClient

class MongoVectorCollection:
    def __init__(self, db, collection_name: str, embedding_function=None):
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name
        self.embedding_function = embedding_function

    def add(self,
            documents: Optional[List[str]] = None,
            embeddings: Optional[List[List[float]]] = None,
            metadatas: Optional[List[Dict]] = None,
            ids: Optional[List[str]] = None):
        """Add documents with embeddings to the collection"""

        if documents is None and embeddings is None:
            raise ValueError("Either documents or embeddings must be provided")

        # Auto-generate embeddings if only documents provided
        if embeddings is None and documents is not None:
            if self.embedding_function is None:
                raise ValueError("No embedding function provided. Cannot embed documents.")
            embeddings = [self.embedding_function.encode(doc) for doc in documents]

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in (documents or embeddings)]

        if metadatas is None:
            metadatas = [{} for _ in (documents or embeddings)]

        if documents is None:
            documents = [""] * len(embeddings)  # Empty strings as placeholders

        docs_to_insert = []
        for i, (doc, embedding, metadata, doc_id) in enumerate(zip(documents, embeddings, metadatas, ids)):
            docs_to_insert.append({
                "_id": doc_id,
                "text": doc,
                "embedding": embedding.tolist(),
                "metadata": metadata
            })

        self.collection.insert_many(docs_to_insert)

    def query(self,
              query_texts: Optional[List[str]] = None,
              query_embeddings: Optional[List[List[float]]] = None,
              n_results: int = 10,
              where: Optional[Dict] = None,
              where_document: Optional[Dict] = None) -> Dict[str, List]:
        """Query similar documents - supports both text and embedding queries"""

        # Handle query_texts by converting to embeddings
        if query_texts is not None:
            if self.embedding_function is None:
                raise ValueError("No embedding function provided. Cannot embed query texts.")
            query_embeddings = [self.embedding_function.encode(text) for text in query_texts]
        elif query_embeddings is None:
            raise ValueError("Either query_texts or query_embeddings must be provided")

        results = {
            'ids': [],
            'distances': [],
            'documents': [],
            'metadatas': []
        }

        for query_embedding in query_embeddings:
            # Build MongoDB filter
            mongo_filter = {}
            if where:
                for key, value in where.items():
                    mongo_filter[f"metadata.{key}"] = value

            if where_document:
                # Simple text search in document field
                if "$contains" in where_document:
                    mongo_filter["document"] = {"$regex": where_document["$contains"], "$options": "i"}

            # Get all documents matching filter
            cursor = self.collection.find(mongo_filter)
            documents = list(cursor)

            if not documents:
                results['ids'].append([])
                results['distances'].append([])
                results['documents'].append([])
                results['metadatas'].append([])
                continue

            # Calculate similarities
            similarities = []
            query_vec = np.array(query_embedding)

            for doc in documents:
                if 'embedding' not in doc:
                    continue

                doc_vec = np.array(doc['embedding'])

                # Cosine similarity (convert to distance: 1 - similarity)
                similarity = np.dot(query_vec, doc_vec) / (
                       np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )

                # similarity = self.embedding_function.similarity(query_vec, [float(x) for x in doc_vec])
                distance = 1 - similarity

                similarities.append({
                    'id': doc['_id'],
                    'distance': distance,
                    'document': doc['text'],
                    'metadata': doc['metadata']
                })

            # Sort by distance (ascending - smaller is more similar)
            similarities.sort(key=lambda x: x['distance'])
            similarities = similarities[:n_results]

            # Format results like Chroma
            results['ids'].append([s['id'] for s in similarities])
            results['distances'].append([s['distance'] for s in similarities])
            results['documents'].append([s['document'] for s in similarities])
            results['metadatas'].append([s['metadata'] for s in similarities])

        return results


# Client with embedding function support
class MongoVectorClient:
    def __init__(self, connection_string: str, database_name: str, collection_name : str, embedding_function=None):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.embedding_function = embedding_function

    def test_client(self):
        try:
            # Send a ping to confirm a successful connection
            self.client.admin.command({'ping': 1})
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error: {e}")

    def generate_all_docs_to_embed(self):
        try:
            # Send a ping to confirm a successful connection
            cursor = self.collection.find({})
            all_results = list(cursor)
            embed_list = []
            for doc in all_results:
                doc_prompt = doc['prompt']
                doc_response = doc['response']
                doc_to_embed = "Prompt: " + doc_prompt + ", Response: " + doc_response
                embed_list.append(doc_to_embed)
            return embed_list
        except Exception as e:
            print(f"Error: {e}")

    def get_or_create_collection(self, name: str) -> MongoVectorCollection:
        """Get or create a collection with embedding function"""
        return MongoVectorCollection(self.db, name, self.embedding_function)
