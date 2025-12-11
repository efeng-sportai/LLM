import keras
import keras_hub
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from mongo_vector_collection import MongoVectorClient, MongoVectorCollection
import kaggle


class LLM:
    def __init__(self, user_query: str, pre_trained_model_path: str, vector_database = None,
                 embeddings_model = None, chat_bot = None):
        self.chat_bot = chat_bot
        self.pre_trained_model_path = pre_trained_model_path
        self.vector_database = vector_database
        self.user_query = user_query
        self.embedded_query = None
        self.model =  None
        self.embeddings_model = embeddings_model

    def load_pretrained_model(self):
        """Load a pre-trained Keras model from the specified path."""
        # We can add as many pretrained models as we would like here
        kaggle.api.authenticate()
        try:
            if self.pre_trained_model_path == "gpt2":
                self.model = keras_hub.models.GPT2CausalLM.from_preset()
            elif self.pre_trained_model_path == "gemma":
                self.model = keras_hub.models.Gemma3CausalLM.from_preset("gemma3_instruct_4b")
            print(f"Model loaded successfully from {self.pre_trained_model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")

    def preprocess_input(self, input_text):
        """Preprocess the input text for the model."""
        # Use this method for embedding the user query
        try:
            self.embedded_query = self.embeddings_model.embed_query(input_text)
            print(f"Embedded query: {self.embedded_query}")
        except Exception as e:
            print(f"Error embedding query: {e}")

    def generate_context(self):
        context_string = ""
        vector_store = MongoDBAtlasVectorSearch.from_connection_string(
            self.vector_database["CONNECTION"],
            self.vector_database["DB_NAME"],
            self.vector_database["COLLECTION"],
            self.vector_database["EMBEDDING_FUNCTION"],
            self.vector_database["INDEX_NAME"],
            self.vector_database["TEXT_KEY"],
            self.vector_database["EMBEDDING_KEY"]
        )
        retriever = vector_store.as_retriever()
        document = retriever.invoke(self.user_query)
        for doc in document:
            context_string = context_string.append(doc.page_content + " ")
        return context_string

    def fine_tuning(self,train_set, val_set, BATCH_SIZE: int, EPOCHS: int, LEARNING_RATE: float):
        try:
            model = self.model
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                metrics=[keras.metrics.SparseCategoricalAccuracy()],
            )
            model.fit(
                train_dataset=train_set,
                validation_data=val_set,
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
            )
        except Exception as e:
            print(f"Error fine tuning model: {e}")

    def generate_text(self, input_context, max_length=300):
        """Generate text using the pre-trained model."""
        if not self.model:
            print("Model is not loaded. Please load a model first.")
            return None

        # Preprocess the input text
        PROMPT_TEMPLATE = (
            "Context:\n{context}\n\n"
            "Question: \n{query}\n\n"
        )

        prompt = PROMPT_TEMPLATE.format(context=input_context, query=self.user_query)
        
        # Debug: Log the prompt template and variables
        print(f"\n{'='*80}")
        print("📝 PROMPT TEMPLATE OBJECT:")
        print(f"{'='*80}")
        print(f"Template String: {PROMPT_TEMPLATE}")
        print(f"\n🔧 ACTIVE VARIABLES:")
        print(f"  - context: {len(input_context)} characters")
        print(f"  - query: {self.user_query}")
        print(f"\n📄 FULL FORMATTED PROMPT (first 1000 chars):")
        print(f"{prompt[:1000]}...")
        print(f"{'='*80}\n")
        
        # Generate report using the text model (text only, no image input)
        output = self.model.generate(
        {
            "prompts": prompt,
        }
        , max_length=max_length
    )
        return output


def main():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    db_username = 'aot3qx'
    db_password = '6994e7MQKos76gRi'
    conn_string = f"mongodb+srv://{db_username}:{db_password}@sportaichat.a1hrgg1.mongodb.net/?appName=SportAIChat"
    database_name = "sportai_documents"
    collection_name = "training_data"
    client = MongoVectorClient(connection_string = conn_string,database_name = database_name,collection_name = collection_name,embedding_function = model)
    client.test_client()
    # docs_to_embed = client.generate_all_docs_to_embed()


    query_test_case =list("What are the top NFL TE players from Sleeper")
    embedding_coll = client.get_or_create_collection(name = 'training_data_embeddings')
    similar_texts = embedding_coll.query(query_texts = query_test_case)
    print(similar_texts['ids'][0])
    print(similar_texts['documents'][0])
    print(similar_texts['distances'][0])
    context = (similar_texts['documents'][0][0])
    #embedding_coll.add(docs_to_embed)

    # Download latest version

    test_llm = LLM(user_query = query_test_case[0], pre_trained_model_path = 'gemma')
    test_llm.load_pretrained_model()
    output = test_llm.generate_text(context)

    print(output)

if __name__ == '__main__':
    main()