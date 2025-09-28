# data_preparation.py - Updated version
import os
import shutil
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from env import CHROMA_COLLECTION_NAME, HF_TOKEN, CHROMA_PATH, TEXT_FILE_DIRECTORY

class DataPreparer:
    def __init__(self, embedding_model="LaBSE"):
        self.embedding_model = embedding_model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model, 
            token=HF_TOKEN
        )
        self.chroma_path = CHROMA_PATH
        self.text_file_directory = TEXT_FILE_DIRECTORY

    def prepare_chroma_db(self, chunk_size=800, chunk_overlap=80):
        """Create and populate the ChromaDB with text embeddings"""
        
        # Clean up existing ChromaDB directory
        if os.path.exists(self.chroma_path):
            print(f"Removing existing ChromaDB directory: {self.chroma_path}")
            shutil.rmtree(self.chroma_path)
        
        print("Initializing ChromaDB client...")
        chroma_client = chromadb.PersistentClient(
            path=self.chroma_path, 
            settings=Settings()  # Remove allow_reset=True for production
        )
        
        # Create fresh collection
        chroma_collection = chroma_client.create_collection(
            CHROMA_COLLECTION_NAME, 
            embedding_function=self.embedding_fn
        )

        print("Loading and chunking text files...")
        for file_idx, file_name in enumerate(os.listdir(self.text_file_directory)):
            if not file_name.endswith(".txt"):
                continue
                
            file_path = os.path.join(self.text_file_directory, file_name)
            with open(file_path, "r", encoding="utf-8") as file:
                text_content = file.read()
            
            # Split text into chunks
            chunks = self._split_text(text_content, chunk_size, chunk_overlap)
            
            # Prepare documents for batch addition
            documents = []
            metadatas = []
            ids = []
            
            for idx, chunk in enumerate(chunks):
                full_idx = f'{file_idx}_{idx}'
                preprocessed_text = f'{file_name[:-4]} - {chunk}'
                
                documents.append(preprocessed_text)
                metadatas.append({"source": "text_file", "file_name": file_name})
                ids.append(full_idx)
            
            # Add in batches to avoid memory issues
            if documents:
                chroma_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            print(f"Processed {file_name}: {len(chunks)} chunks")

        print(f"ChromaDB preparation complete! Database saved to: {self.chroma_path}")

    def _split_text(self, text, chunk_size, chunk_overlap):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
            if start >= len(text):
                break
        return chunks

if __name__ == "__main__":
    preparer = DataPreparer()
    preparer.prepare_chroma_db(chunk_size=800, chunk_overlap=80)
