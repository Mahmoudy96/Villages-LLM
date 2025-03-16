from langchain_community.document_loaders.mongodb import MongodbLoader
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
from env import mongodb_URI

# Load data from MongoDB
loader = MongodbLoader(
    connection_string=mongodb_URI,
    db_name='Villages',
    collection_name='villageStats',
    field_names=[
        'District', 'Village', 'Population_1945_Arabs',
        'Population_1945_Jews','Population_1945_Total', 'Total_Land_Areas_Dunums_Arabs',
        'Total_Land_Areas_Dunums_Jews', 'Total_Land_Areas_Dunums_Public'
    ]
)

documents = loader.load()

# Convert MongoDB documents into plain text for vector storage
formatted_docs = []
for doc in documents:
    metadata = doc.metadata  # MongoDB metadata
    content = doc.page_content  # Raw text
    
    # Ensure structured numerical data is formatted into text
    structured_text = f"Village: {metadata.get('Village', 'Unknown')}, District: {metadata.get('District', 'Unknown')}, "
    structured_text += f"Arab Population (1945): {metadata.get('Population_1945_Arabs', 'N/A')}, "
    structured_text += f"Jewish Population (1945): {metadata.get('Population_1945_Jews', 'N/A')}, "
    structured_text += f"Land Owned by Arabs (dunums): {metadata.get('Total_Land_Areas_Dunums_Arabs', 'N/A')}, "
    structured_text += f"Land Owned by Jews (dunums): {metadata.get('Total_Land_Areas_Dunums_Jews', 'N/A')}, "
    structured_text += f"Public Land (dunums): {metadata.get('Total_Land_Areas_Dunums_Public', 'N/A')}"
    
    formatted_docs.append(Document(page_content=structured_text, metadata=metadata))

# Load Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create a FAISS vectorstore
vectorstore = FAISS.from_documents(formatted_docs, embeddings)

# Query
query = "What is the population of Nazareth in 1945?"
results = vectorstore.similarity_search(query, k=5)

# Display results
for res in results:
    print(res.page_content)
