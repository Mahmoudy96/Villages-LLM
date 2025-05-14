import os
from pymongo import MongoClient
import chromadb
from chromadb.utils import embedding_functions
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # For using open-source LLMs
from DocumentManagement.NormalizeArabicText import preprocess_arabic_text
from openai import OpenAI
#import arabic_reshaper
#from bidi.algorithm import get_display
from env import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME, CHROMA_COLLECTION_NAME, HF_TOKEN,OPENAI_API_KEY, TEXT_FILE_DIRECTORY,CHROMA_PATH
#from langchain.llms import HuggingFacePipeline
#from petals import AutoDistributedModelForCausalLM
#from huggingface_hub import InferenceClient


class RAGLLM:
    def __init__(self, token=HF_TOKEN, text_file_directory=TEXT_FILE_DIRECTORY, openai_api_key=OPENAI_API_KEY):
        self.llm = None
        self.token=token
        self.openai_api_key=openai_api_key
        self.text_file_directory = text_file_directory
        self.chunk_size=200
        self.chunk_overlap=20
        self.mongo_client = None
        self.db = None
        self.collection = None
        self.chroma_client = None
        self.chroma_collection = None   
        self.embedding_model = None 
        self.embedding_fn = None
        self.natural_language_query = None
        self.query_translator = None

    def initialize_db(self, mongo_uri=MONGODB_URI, database_name=DATABASE_NAME, collection_name=COLLECTION_NAME):
        print(f"Connecting to MongoDB at {mongo_uri}")
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[database_name]
        self.collection = self.db[collection_name]
        self.query_translator = pipeline("text2text-generation", model="google/flan-t5-large")


    def initialize_embedding_model(self, embedding_model="all-MiniLM-L6-v2", chroma_collection_name=CHROMA_COLLECTION_NAME,chroma_path=CHROMA_PATH,chunk_size=200, chunk_overlap=20):
        print(f"Initializing ChromaDB with embedding model: {embedding_model}")
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)#.Client()
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        self.chroma_collection = self.chroma_client.get_or_create_collection(chroma_collection_name, embedding_function=embedding_fn)
        self.load_and_chunk_text_to_chroma()

    def initialize_llm(self, model_name="google/gemma-2b", temperature=0.7, max_length=500):
        print(f"Initializing LLM with model: {model_name}")
        '''self.llm = HuggingFacePipeline.from_pretrained(
            model_name,
            model_kwargs={
                "temperature": temperature,
                "max_length": max_length
            },
            huggingfacehub_api_token=self.token,
        )    
        '''
        self.model_name = model_name
        #self.tokenizer = AutoTokenizer.from_pretrained(model_name,token=self.token)
        #self.model = AutoModelForCausalLM.from_pretrained(model_name,token=self.token)
        #self.llm = InferenceClient(model=model_name, token=self.token)
        #self.llm = pipeline("text-generation", model=self.model,max_new_tokens=2048 ,tokenizer=self.tokenizer, device=0,token=self.token)  # Use GPU if available
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def split_text(self, text):
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        return chunks
    
    def load_and_chunk_text_to_chroma(self):
        for file_idx,file_name in enumerate(os.listdir(self.text_file_directory)):
            if not file_name.endswith(".txt"):
                continue
            file_path = os.path.join(self.text_file_directory, file_name)
            print(file_path)
            with open(file_path, "r", encoding="utf-8") as file:
                #text_data = []
                #for text in file.read().splitlines():
                #    if len(text)<100:
                #        continue
                #    text_data += split_text(text,chunk_size,chunk_overlap)
                text_data = self.split_text( file.read())
            existing_ids = set(self.chroma_collection.get()["ids"])
            for idx, text in enumerate(text_data):
                full_idx = str(f'{file_idx}_{idx}')
                if full_idx in existing_ids:
                    continue
                preprocessed_text = f'{file_name[:-4]} - {text}'#remove .txt from the end #preprocess_arabic_text(text)  
                #print(idx, file_name)
                #print(get_display(arabic_reshaper.reshape(preprocessed_text)))
                self.chroma_collection.add(
                documents=[preprocessed_text],
                metadatas=[{"source": "text_file"}],
                ids=[full_idx]
                )

                
                
    def translate_to_mongo_query(self):
        schema_info = """
            The MongoDB collection has the following fields:
            - "metadata.name"
            - "metadata.district"
            - "metadata.coordinates.lat"
            - "metadata.coordinates.long"
            - "history.occupation_date"
            - "history.exodus_cause"
            - "history.military_operation"
            """
        prompt = f"""
        Translate the following natural language query into a MongoDB find query. Use the schema information provided below:

        Schema Information:
        {schema_info}

        Natural Language Query: {self.natural_language_query}

        Don't include this query in the response, only the MongoDB query.
        Give the answer as a mongodb query in the format
        {{"fieldname":"value"}}
        """
        #print(f"Query Translation Prompt: {prompt}")
        translated_query = self.query_translator(prompt, max_length=2000)[0]['generated_text']
        return translated_query.strip()
    

    def set_natural_language_query(self, query):
        self.natural_language_query = query

    def get_response(self, question: str) -> str:
        """Get response from LLM"""
        if not self.llm_chain:
            return "LLM not initialized properly"
        
        try:
            return self.llm_chain.run(question)
        except Exception as e:
            return f"Error generating response: {str(e)}"
        
    def perform_rag(self):
        # Step 1: Translate natural language query to MongoDB query
        mongo_query = self.translate_to_mongo_query()
        print(f"Translated MongoDB Query: {mongo_query}")

        # Step 2: Retrieve relevant data from MongoDB
        try:
            mongo_results = self.collection.find(eval(mongo_query))  # Use eval to convert string to dict (be cautious with this in production)
            mongo_data = [doc for doc in mongo_results]
        except Exception as e:
            print(f"Error executing MongoDB query: {e}")
            mongo_data = []

        # Step 3: Retrieve relevant text from ChromaDB
        chroma_results = self.chroma_collection.query(
            query_texts=[self.natural_language_query],
            n_results=5  # Number of relevant text chunks to retrieve
        )
        chroma_data = chroma_results["documents"][0]

        # Step 4: Combine data from both sources
        combined_data = {
            "mongo_data": mongo_data,
            "chroma_data": chroma_data
        }

        # Step 5: Generate a prompt for the LLM
        #TODO: Add to the prompt a line to ensure that the question is related to the data provided, and not just a random question.
        prompt = f"""
        You are an AI assistant that answers questions based on the following data:

        MongoDB Data:
        {combined_data['mongo_data']}

        Text Data:
        {combined_data['chroma_data']}

        Please answer the following query based on the statistics provided from MongoDB and the Text Data provided: {self.natural_language_query}
        If you cannot find an answer within the provided data, please respond with "I don't know".
        """
        print(f"Prompt: {prompt}")
        # Step 6: Query the  LLM
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
        #response = self.llm(prompt)[0]['generated_text']#)
        #return response
    

if __name__ == "__main__":
    rag_llm = RAGLLM()
    rag_llm.initialize_db()
    rag_llm.initialize_embedding_model()
    rag_llm.initialize_llm(model_name="gpt-4.1-nano")#"gpt2")
    rag_llm.set_natural_language_query("Give me an essay about the history of the Palestinian people")
    response = rag_llm.perform_rag()
    print(response)

    #rag_llm = pipeline("text-generation", model="google/gemma-3-27b-it",token=HF_TOKEN)  # Example: GPT-2 for RAG (replace with your preferred model)
    #model_name="google/gemma-3-4b-it"
    #model_name="meta-llama/Llama-3.1-8B"
