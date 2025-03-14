import pandas as pd
from pymongo import MongoClient
from env import mongodb_URI

# Load your cleaned data
clean_file_path = './Data/cleaned_Village_data.xlsx'  # Replace with your file path
df = pd.read_excel(clean_file_path)  # Use pd.read_excel() if it's an Excel file

# Convert the DataFrame to a list of dictionaries (MongoDB documents)
data = df.to_dict('records')

# Connect to MongoDB
client = MongoClient(mongodb_URI)  # Replace with your MongoDB connection string
db = client['Villages']  # Replace with your database name
collection = db['villageStats']  # Replace with your collection name

# Insert data into MongoDB
collection.insert_many(data)

print(f"Inserted {len(data)} documents into MongoDB.")