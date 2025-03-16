from langchain_community.document_loaders.mongodb import MongodbLoader
#from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from env import mongodb_URI
from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer

loader = MongodbLoader(
    connection_string=mongodb_URI,
    db_name='Villages',  # Replace with your database name
    collection_name='villageStats',    # Replace with your collection name
    field_names=['District', 'Village', 'Population_1945_Arabs','Population_1945_Jews','Total_Land_Areas_Dunums_Arabs','Total_Land_Areas_Dunums_Jews','Total_Land_Areas_Dunums_Public']  # Fields to load
)

# Load documents from MongoDB
documents = loader.load()

model = SentenceTransformer('all-MiniLM-L6-v2')
# Example: Create embeddings and store them in a vector database
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") #model.encode(["What is the population of Acre in 1945?"])
vectorstore = FAISS.from_documents(documents, embeddings)

# Now you can query the vectorstore
query = "What is the population of Nazareth in 1945?"
results = vectorstore.similarity_search(query)
print(results)