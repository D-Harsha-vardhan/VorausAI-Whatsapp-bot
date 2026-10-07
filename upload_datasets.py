import os
import pandas as pd
from sqlalchemy import create_engine

# ==============================================================================
# IMPORTANT: Replace this with your actual Supabase PostgreSQL connection string!
# You can find it in Supabase Dashboard -> Project Settings -> Database -> Connection string -> URI
# Example: "postgresql://postgres.ovapetxhquabhjmmrhaq:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
# ==============================================================================
DB_CONNECTION_STRING = "postgresql+psycopg2://postgres:kanupsharma123@db.ovapetxhquabhjmmrhaq.supabase.co:5432/postgres"

def upload_csv_to_supabase(directory_path):
    print("Connecting to Supabase Database...")
    try:
        engine = create_engine(DB_CONNECTION_STRING)
        # Test connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Failed to connect to database. Error: {e}")
        return

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                
                # Format table name: remove .csv, convert to lowercase, remove numbers, replace spaces
                table_name = file.replace('.csv', '').lower()
                # Clean up names like "02_programs_masters" -> "programs_masters"
                while table_name and table_name[0].isdigit() or table_name[0] == '_':
                    table_name = table_name[1:]
                
                print(f"Reading {file}...")
                try:
                    # Read the CSV
                    df = pd.read_csv(file_path)
                    
                    print(f"Uploading to table '{table_name}'...")
                    # Upload to Supabase! This automatically creates the table and infers the correct datatypes!
                    df.to_sql(table_name, engine, if_exists='replace', index=False)
                    print(f"Successfully uploaded '{table_name}'!\n")
                except Exception as e:
                    print(f"Error uploading {file}: {e}\n")

if __name__ == "__main__":
    dataset_dir = r"c:\Users\Anupam\Desktop\antigravity projects\Educaro WhatsApp bot\educaro datasets"
    upload_csv_to_supabase(dataset_dir)
