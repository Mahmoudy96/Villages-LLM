import os
import json
from pymongo import MongoClient
import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from transformers import pipeline
from openai import OpenAI
from env import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, CHROMA_COLLECTION_NAME, HF_TOKEN, OPENAI_API_KEY, TEXT_FILE_DIRECTORY, CHROMA_PATH
local_model_path = "./models/LaBSE"

class MongoDBManager:
    def __init__(self, embedding_fn, mongo_uri=MONGODB_URI, database_name=DATABASE_NAME, collection_name=COLLECTION_NAME, ):
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[database_name]
        self.collection = self.db[collection_name]
        self.query_translator = None
        self.current_query = None
        self.embedding_fn = embedding_fn

    def initialize_query_translator(self, use_openAI=False, openai_client=None):
        self.openai_client = openai_client
        if not use_openAI:
            self.query_translator = pipeline("text2text-generation", model="google/flan-t5-large")

    def get_field_names(self, document, prefix=''):
        """Recursively get all field names from a MongoDB document"""
        field_names = []
        for key, value in document.items():
            if isinstance(value, dict):
                field_names.extend(self.get_field_names(value, f"{prefix}{key}."))
            else:
                field_names.append(f"{prefix}{key}")
        return field_names

    def _set_query(self, query):
        """Set the current natural language query"""
        self.current_query = query

    def _find_closest_name(self, names):
        """Vector-based name matching"""
        chroma_client = chromadb.Client(settings=Settings(allow_reset=True))
        chroma_collection = chroma_client.get_or_create_collection(
            "db_names_collection",
            embedding_function=self.embedding_fn 
        )
        chroma_collection.add(
            documents=names,
            metadatas=[{"source": "name_list"}] * len(names),
            ids=[str(i) for i in range(len(names))]
        )
        results = chroma_collection.query(
            query_texts=[self.current_query],
            n_results=1
        )
        return results['documents'][0][0]
        #name_embeddings = self.embedding_fn.encode(self.names)
        #query_embedding = self.embedding_fn.encode([query])
        #similarities = np.dot(query_embedding, name_embeddings.T)
        #return self.names[np.argmax(similarities)]

    def _generate_translation_prompt(self):
        """Generate the prompt for translating natural language to MongoDB query"""
        names = self.collection.distinct("metadata.name")
        closest_name = self._find_closest_name(names)

        random_object = self.collection.find_one()
        fields = self.get_field_names(random_object)

        return f"""
        Your goal is to provide me with a MongoDB query in pymongo format that can be used to retrieve data from a MongoDB collection.
        Based on this Natural Language Query in English, Arabic or Hebrew: {self.current_query}
        The query should select the projection of up to 10 of the most relevant fields from the following list of fields: {fields}
        The query should be for the document with the metadata.name {closest_name}.
        Print the query in a single line as a JSON string, with fields query and projection, without any additional text or formatting. Have _id:0 in the projection.
        example output:
        {{"query": {{"metadata.name": "{closest_name}"}}, "projection": {{"_id": 0, "field1": 1, "field2": 1}}}}
        """

    def _translate_with_openai(self, prompt):
        """Use OpenAI to translate natural language to MongoDB query"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that translates natural language to MongoDB queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more deterministic queries
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI translation error: {str(e)}")

    def _translate_to_mongo_query(self):
        """Translate the current natural language query to a MongoDB query"""
        if not self.current_query:
            raise ValueError("No query set. Call set_query() first.")

        prompt = self._generate_translation_prompt()
        
        if self.query_translator is None:
            if not hasattr(self, 'openai_client'):
                raise ValueError("OpenAI client not initialized. Call initialize_query_translator() with use_openAI=True.")
            translated_query = self._translate_with_openai(prompt)
        else:
            translated_query = self.query_translator(prompt, max_length=2000)
        
        return translated_query

    def _execute_query(self, query_json):
        """Execute a MongoDB query from a JSON string"""
        try:
            query_dict = json.loads(query_json)
            if not all(key in query_dict for key in ['query', 'projection']):
                raise ValueError("Invalid query format. Must contain 'query' and 'projection' keys")
            
            results = list(self.collection.find(
                query_dict['query'],
                query_dict['projection']
            ))
            return results
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON query: {str(e)}")
        except Exception as e:
            raise Exception(f"Query execution error: {str(e)}")

    def get_documents_by_query(self, natural_language_query):
        """Complete pipeline: translate natural language query and execute MongoDB query"""
        self._set_query(natural_language_query)
        mongo_query = self._translate_to_mongo_query()
        return self._execute_query(mongo_query)

class VectorDBManager:
    def __init__(self, embedding_fn, chroma_collection_name=CHROMA_COLLECTION_NAME, 
                 chroma_path=CHROMA_PATH, text_file_directory=TEXT_FILE_DIRECTORY):
        self.chroma_client = chromadb.PersistentClient(path=chroma_path, settings=Settings(allow_reset=True))
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            chroma_collection_name, 
            embedding_function=embedding_fn
        )
        self.text_file_directory = text_file_directory

    def split_text(self, text,chunk_size , chunk_overlap):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def load_and_chunk_text_to_chroma(self,chunk_size=800, chunk_overlap=80):
        for file_idx, file_name in enumerate(os.listdir(self.text_file_directory)):
            if not file_name.endswith(".txt"):
                continue
            file_path = os.path.join(self.text_file_directory, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                text_data = self.split_text(file.read(),chunk_size,chunk_overlap)
            existing_ids = set(self.chroma_collection.get()["ids"])
            for idx, text in enumerate(text_data):
                full_idx = str(f'{file_idx}_{idx}')
                if full_idx in existing_ids:
                    continue
                preprocessed_text = f'{file_name[:-4]} - {text}'
                self.chroma_collection.add(
                    documents=[preprocessed_text],
                    metadatas=[{"source": "text_file"}],
                    ids=[full_idx]
                )

    def query_text(self, query_text, n_results=5):
        return self.chroma_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

class LLMChatbot:
    def __init__(self, model_name="gpt-4.1-mini", openai_api_key=OPENAI_API_KEY):
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=openai_api_key)

    def set_model(self, model_name):
        self.model_name = model_name

    def generate_response(self, mongo_data, chroma_data, user_query,history_summary=None):
        prompt = f"""
        You are an AI assistant that answers questions based on the following data:
        {history_summary if history_summary else "No previous conversation history."}
        
        The answer must be as detailed as possible based on the context you are provided in this prompt, and in the language you were asked in. 
        Give less detailed answers if the question is general, or if the context does not seem related to the question.
        DO NOT refer to the context or data, just answer the question based on them.
        
        If you are asked about yourself, tell the user that you are the Rahalah AI assistant, and you are here to help them with their questions.
        
        If the answer is not included in the provided context:
        1. Apologize to the user in the language you were asked.
        2. Tell them that you are an AI assistant and you are here to help them with their questions.
        3. Ask them to ask a different question or use different wording.
        4. Do not mention the context or the knowledge base, just say that you are an AI assistant and you are here to help them with their questions.
        5. If you are told 'افصع', answer: يفوت وما يطلع

        Statistics/Information Data:
        {mongo_data}

        Text Data:
        {chroma_data}

        Question: {user_query}
        """
        
        print("Prompt:", prompt)

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"

class RAGSystem:
    def __init__(self, embedding_model="laBSE"):
        self.embedding_model = embedding_model
        if os.path.exists(local_model_path):
            print("Using local model path for embedding.")
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=local_model_path)
        else:
            print("Local model path not found. Using Hugging Face model.")
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model,use_auth_token=HF_TOKEN)
        self.mongo_manager = MongoDBManager(self.embedding_fn)
        self.vector_db_manager = VectorDBManager(self.embedding_fn)
        self.chatbot = LLMChatbot()

    def initialize_components(self, use_openAI=True,chunk_size=800, chunk_overlap=80):
        self.mongo_manager.initialize_query_translator(use_openAI=use_openAI, openai_client=self.chatbot.openai_client)
        self.vector_db_manager.load_and_chunk_text_to_chroma(chunk_size, chunk_overlap)

    def process_query(self, query,summary=None):
        # Get data from MongoDB
        mongo_data = self.mongo_manager.get_documents_by_query(query)
        print(f"MongoDB Data: {mongo_data}")
        # Get relevant text chunks from vector DB
        chroma_results = self.vector_db_manager.query_text(query)
        chroma_data = chroma_results["documents"][0]
        print(f"Chroma Data: {chroma_data}")
        # Generate response
        return self.chatbot.generate_response(mongo_data, chroma_data, query,summary)

if __name__ == "__main__":
    rag_system = RAGSystem()

    rag_system.initialize_components(use_openAI=True, chunk_size=800, chunk_overlap=80)
    rag_system.chatbot.set_model("gpt-4.1-mini")

    query = "اعطيني معلومات عن حياة سكان الزيب"

    response = rag_system.process_query(query)
    print(response)