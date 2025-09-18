import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI=os.getenv("MONGODB_URI")
DATABASE_NAME = "Villages"
COLLECTION_NAME = "villageStatistics"
CHROMA_COLLECTION_NAME = "VillageDocuments"
TEXT_FILE_DIRECTORY = "./Data/Documents"
CHROMA_PATH = "./chroma_data"
HF_TOKEN=os.getenv("HF_TOKEN")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")  
BACKEND_URL=os.getenv("BACKEND_URL")