import os
import json
from pymongo import MongoClient
import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from transformers import pipeline
from openai import OpenAI
from env import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, CHROMA_COLLECTION_NAME, HF_TOKEN, OPENAI_API_KEY, CHROMA_PATH
import asyncio
from functools import lru_cache
import hashlib

try:
    from rag_logger import log_mongo_query, log_chroma_result, log_llm_context, log_error
    _LOGGING_ENABLED = True
except ImportError:
    _LOGGING_ENABLED = False

class MongoDBManager:
    def __init__(self, embedding_fn, mongo_uri=MONGODB_URI, database_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
        self.mongo_client = None
        self.db = None
        self.collection = None
        self.query_translator = None
        self.current_query = None
        self.embedding_fn = embedding_fn
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.collection_name = collection_name
        
        # Try to connect, but don't fail if MongoDB is not available
        if mongo_uri:
            try:
                self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                self.db = self.mongo_client[database_name]
                self.collection = self.db[collection_name]
                # Test connection
                self.mongo_client.server_info()
                print("[OK] MongoDB connected successfully")
            except Exception as e:
                print(f"[WARNING] MongoDB connection failed: {str(e)}")
                print("   Continuing without MongoDB - some features may be limited")
                self.mongo_client = None

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
        if not names:
            return None
        try:
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
            return results['documents'][0][0] if results['documents'] and results['documents'][0] else names[0]
        except Exception as e:
            print(f"[WARNING] Error in _find_closest_name: {str(e)}")
            return names[0] if names else None

    def _generate_translation_prompt(self):
        """Generate the prompt for translating natural language to MongoDB query"""
        if not self.collection:
            raise ValueError("MongoDB collection not available")
        
        names = self.collection.distinct("metadata.name")
        closest_name = self._find_closest_name(names) if names else "unknown"

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
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that translates natural language to MongoDB queries."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=8000
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
        if not self.mongo_client or not self.collection:
            print("[WARNING] MongoDB not available, returning empty results")
            return []
        
        self._set_query(natural_language_query)
        mongo_query = self._translate_to_mongo_query()
        results = self._execute_query(mongo_query)
        if _LOGGING_ENABLED:
            log_mongo_query(mongo_query, results, natural_language_query)
        return results

class VectorDBManager:
    def __init__(self, embedding_fn, chroma_collection_name=CHROMA_COLLECTION_NAME, 
                 chroma_path=CHROMA_PATH):
        # Note: No text_file_directory needed here - we only read from pre-built DB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path, settings=Settings(allow_reset=True))
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            chroma_collection_name, 
            embedding_function=embedding_fn
        )

    def query_text(self, query_text, n_results=5):
        """Query the pre-built ChromaDB"""
        results = self.chroma_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        if _LOGGING_ENABLED:
            docs = results.get("documents", [[]])[0] if results else []
            metas = results.get("metadatas", [[]])[0] if results.get("metadatas") else None
            dists = results.get("distances", [[]])[0] if results.get("distances") else None
            log_chroma_result(query_text, docs, metas, dists)
        return results

class LLMChatbot:
    def __init__(self, model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY):  # Fixed: Changed from invalid "gpt-5-nano" to valid model
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=openai_api_key)

    def set_model(self, model_name):
        self.model_name = model_name

    async def generate_response(self, mongo_data, chroma_data, user_query, history_summary=None, stream=False, on_token=None):
        if _LOGGING_ENABLED:
            log_llm_context(user_query, mongo_data, chroma_data, history_summary)
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
        
        #print("Prompt:", prompt)

        try:
            loop = asyncio.get_event_loop()
            if not stream:
                def sync_call():
                    response = self.openai_client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        max_completion_tokens=8000
                    )
                    return response.choices[0].message.content
                return await loop.run_in_executor(None, sync_call)
            else:
                tokens_list = []
                def sync_stream():
                    stream_resp = self.openai_client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        max_completion_tokens=8000,
                        stream=True
                    )
                    for event in stream_resp:
                        try:
                            choice = event.choices[0]
                            delta = getattr(choice, "delta", None)
                            if delta is None:
                                continue
                            token = getattr(delta, "content", None)
                            if token:
                                tokens_list.append(token)
                                print(token, end="", flush=True)
                        except Exception:
                            continue
                    print("")
                
                await loop.run_in_executor(None, sync_stream)
                full_text = "".join(tokens_list)
                if on_token:
                    for token in tokens_list:
                        if asyncio.iscoroutinefunction(on_token):
                            await on_token(token)
                        else:
                            on_token(token)
                return full_text
        except Exception as e:
            return f"Error: {str(e)}"


class RAGSystem:
    def __init__(self, embedding_model="LaBSE"):
        self.embedding_model = embedding_model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model, 
            token=HF_TOKEN
        )
        self.mongo_manager = MongoDBManager(self.embedding_fn)
        self.vector_db_manager = VectorDBManager(self.embedding_fn)
        self.chatbot = LLMChatbot()
        self._query_cache = {}  # Simple dict cache

    def initialize_components(self, use_openAI=True):
        self.mongo_manager.initialize_query_translator(use_openAI=use_openAI, openai_client=self.chatbot.openai_client)

    async def process_query(self, query, summary=None, stream=False, on_token=None):
        """Async pipeline: translate query, run DB lookups (in parallel) and generate response."""
        
        # Check cache first (simple optimization for identical queries)
        cache_key = hashlib.md5(f"{query}".encode()).hexdigest()
        if cache_key in self._query_cache:
            cached_response = self._query_cache[cache_key]
            if on_token and stream:
                # Yield cached response token-by-token
                for token in cached_response.split():
                    if asyncio.iscoroutinefunction(on_token):
                        await on_token(token + " ")
                    else:
                        on_token(token + " ")
            return cached_response
        
        loop = asyncio.get_event_loop()
        
        # Run MongoDB and Chroma queries in PARALLEL instead of sequentially
        mongo_task = loop.run_in_executor(None, self.mongo_manager.get_documents_by_query, query)
        chroma_task = loop.run_in_executor(None, self.vector_db_manager.query_text, query)
        
        # Wait for both to complete
        mongo_data, chroma_results = await asyncio.gather(mongo_task, chroma_task)
        chroma_data = chroma_results.get("documents", [[]])[0] if chroma_results else []
        
        # Generate response
        response = await self.chatbot.generate_response(mongo_data, chroma_data, query, summary, stream=stream, on_token=on_token)
        
        # Cache the response (only cache non-streaming for simplicity)
        if not stream:
            self._query_cache[cache_key] = response
            # Keep cache size bounded (max 100 entries)
            if len(self._query_cache) > 100:
                self._query_cache.pop(next(iter(self._query_cache)))
        
        return response

    def process_query_sync(self, query, summary=None, stream=False, on_token=None):
        return asyncio.run(self.process_query(query, summary=summary, stream=stream, on_token=on_token))

if __name__ == "__main__":
    rag_system = RAGSystem()
    rag_system.initialize_components(use_openAI=True)
    rag_system.chatbot.set_model("gpt-4o-mini")  # Fixed: Changed from invalid "gpt-5-nano" to valid model

    query = "اعطيني معلومات عن حياة سكان الزيب"

    #Example: stream to console using the sync wrapper
    print("Streaming response:")
    response = rag_system.process_query_sync(query, stream=True)
    
    print("\nFinal response (collected):")
    print(response)