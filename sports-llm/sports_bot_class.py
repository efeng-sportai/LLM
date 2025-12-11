from mongo_vector_collection import MongoVectorClient, MongoVectorCollection

class sports_bot:
    def __init__(self, time_of_creation, user_question, answer_to_question):
        self.user_question = user_question
        self.answer_to_question = answer_to_question
        self.time_of_creation = time_of_creation

    def get_mongo_collection(self):
        client = MongoVectorClient(
            "mongodb+srv://<username>:<password>@cluster0.mongodb.net/test?retryWrites=true&w=majority",
            "mongo_db",
            embedding_function=self.simple_embedding_function
        )
        collection = client.get_or_create_collection("sports_bot")
        return collection

    def get_user_question(self):
        return self.user_question

    def get_answer_to_question(self):
        return self.answer_to_question

    def get_time_of_creation(self):
        return self.time_of_creation

    def get_system_prompt(self):
        return 'Placeholder system prompt that gets passed along with the user question'

    def __str__(self):
        return f"User Question: {self.user_question}, Answer to Question: {self.answer_to_question}, Time of Creation: {self.time_of_creation}"

    def upload_to_mongo(self):
        upload_dict = [{"user_question": self.user_question, "answer_to_question": self.answer_to_question,
                        "time_of_creation": self.time_of_creation}]

        collection = self.get_mongo_collection()

        # example of us uploading things, could be some type of sports data
        collection.add(
            documents=["This is document 1", "This is document 2"],
            metadatas=[{"source": "web"}, {"source": "book"}],
            ids=["doc1", "doc2"]
        )

        results = collection.query(
            query_texts=[self.get_user_question],  # Raw text query
            n_results=5
        )

        # Or query with embeddings (we can use the simple function below or use an LLM)
        # results = collection.query(
        #     query_embeddings=[[0.1, 0.2, 0.3, ...]],
        #     n_results=2
        # )

        return results

    # Example embedding function (you'd use a real one like OpenAI, Sentence Transformers, etc.)
    def simple_embedding_function(text: str) -> list[float]:
        # This is just a dummy - use a real embedding model
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(text).tolist()
