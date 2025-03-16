from pymongo import MongoClient
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from env import mongodb_URI

# Connect to MongoDB
client = MongoClient(mongodb_URI)
db = client['Villages']
collection = db['villageStats']

# Fetch data from MongoDB
data = collection.find({}, {
    'District': 1,
    'Village': 1,
    'Population_1945_Arabs': 1,
    'Population_1945_Jews': 1,
    'Total_Land_Areas_Dunums_Arabs': 1,
    'Total_Land_Areas_Dunums_Jews': 1,
    'Total_Land_Areas_Dunums_Public': 1
})#.limit(100)  # Adjust the limit as needed

# Convert MongoDB documents to LangChain Documents
documents = []
for doc in data:
    content = f"""
    District: {doc['District']}
    Village: {doc['Village']}
    Population (Arabs, 1945): {doc['Population_1945_Arabs']}
    Population (Jews, 1945): {doc['Population_1945_Jews']}
    Total Land Areas (Arabs): {doc['Total_Land_Areas_Dunums_Arabs']}
    Total Land Areas (Jews): {doc['Total_Land_Areas_Dunums_Jews']}
    Total Land Areas (Public): {doc['Total_Land_Areas_Dunums_Public']}
    """
    documents.append(Document(page_content=content, metadata=doc))

print(f"Loaded {len(documents)} documents.")

# Initialize Hugging Face embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create the vector store
vectorstore = FAISS.from_documents(documents, embeddings)

print("Vector store created successfully.")

# Query the vector store
query = "What is the population of Nazareth in 1945?"
query = "What is the population of Hadatha in 1945?"
arabic_query = "ما عدد سكان نابلس في عام 1945؟"
#results = vectorstore.similarity_search(arabic_query)
results = vectorstore.similarity_search(query)

# Print the results
for result in results:
    print(result.page_content)
    print(result.metadata)
    print("---")