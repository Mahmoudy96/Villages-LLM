import pandas as pd
from langchain_community.document_loaders.mongodb import MongodbLoader

from pymongo import MongoClient
from env import mongodb_URI

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
if not documents:
    raise ValueError("No documents were loaded from MongoDB. Check database connection and field names.")
