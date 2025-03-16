import pandas as pd
from pymongo import MongoClient
from env import mongodb_URI

def transform_village_data(df):
    """Transform flat dataframe into nested documents with cleaned metadata"""
    transformed = []
    
    for _, row in df.iterrows():
        # Extract base information
        village_id = row["ID"]
        village_name = row["Village"].split("(")[0].strip()
        district = row["District"]
        
        # Handle alternative names/notes in parentheses
        alt_names = []
        if "(" in row["Village"]:
            notes = row["Village"].split("(")[1].replace(")", "").strip()
            alt_names = [n.strip() for n in notes.split(",") if n.strip()]
        
        # Build nested document
        doc = {
            "metadata": {
                "id": village_id,
                "name": village_name,
                "district": district,
                "alt_names": alt_names,
                "coordinates": {
                    "lat": row["Latitude"],
                    "lon": row["Longitude"]
                }
            },
            "demographics": {
                "population": {
                    "year_1945": {
                        "arabs": row["Population_1945_Arabs"],
                        "jews": row["Population_1945_Jews"],
                        "total": row["Population_1945_Total"]
                    }
                }
            },
            "geography": {
                "land": {
                    "total_dunums": row["Total_Land_Areas_Dunums_Total"],
                    "cultivable": {
                        "citrus_banana": row["Cultivable_Land_Areas_in_Dunums_Citrus_&_Banana_Land_Total"],
                        "irrigated": row["Cultivable_Land_Areas_in_Dunums_Irrigated_&_Plantation_Land_Total"],
                        "cereal": row["Cultivable_Land_Areas_in_Dunums_Cereal_Land_Total"]
                    }
                }
            },
            "history": {
                "occupation_date": row.get("Occupation_Date", None),
                "exodus_cause": row.get("Exodus_Cause", None),
                "military_operation": row.get("Israeli_Operation_CD", None)
            }
        }
        
        # Add optional fields only if they exist
        if pd.notna(row.get("No._of_Schools")):
            doc["community"] = {
                "facilities": {
                    "schools": row["No._of_Schools"],
                    "mosques": row.get("No._of_Mosques", None),
                    "churches": row.get("No._of_Churches", None)
                }
            }
        
        transformed.append(doc)
    
    return transformed

# Example usage
if __name__ == "__main__":
    # Load data
    df = pd.read_excel('./Data/cleaned_Village_data.xlsx')
    
    # Transform data
    village_docs = transform_village_data(df)
    
    # Connect to MongoDB
    client = MongoClient(mongodb_URI)
    db = client['Villages']
    
    # Insert transformed data
    db.villageStatistics.drop()  # Clear existing data  
    db.villageStatistics.insert_many(village_docs)
    print(f"Successfully inserted {len(village_docs)} transformed village documents")