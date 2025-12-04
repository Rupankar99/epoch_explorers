import os
import sqlite3
import pandas as pd
import json
from pathlib import Path

# New: Read configuration
import yaml

def load_config(config_path):
    """Load configuration from a YAML file."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def identify_and_parse_data(config):
    """Identify and parse files based on the configuration."""
    parsed_data = []

    for entry in config['data_sources']:
        data_dir = Path(entry['path'])
        file_pattern = entry.get('file_name', '*')

        for file in data_dir.glob(file_pattern):
            if file.suffix == '.csv':
                df = pd.read_csv(file)
                parsed_data.append((file.stem, df))
            elif file.suffix == '.json':
                with open(file, 'r') as f:
                    data = json.load(f)
                    df = pd.DataFrame(data)
                    parsed_data.append((file.stem, df))

    return parsed_data

def save_to_sqlite(parsed_data, db_path):
    """Save parsed data to SQLite tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table_name, df in parsed_data:
        df.to_sql(table_name, conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

def perform_clustering(db_path, table_name, cluster_table_name):
    """Perform clustering on the data and save results to a new table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load data from the specified table
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

    # Example clustering logic (replace with actual clustering algorithm)
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=3)
    df['cluster'] = kmeans.fit_predict(df.select_dtypes(include=['float64', 'int64']))

    # Save clustered data to a new table
    df.to_sql(cluster_table_name, conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    config_path = "src/clusterer/config.yaml"
    db_path = "src/clusterer/cluster_data.db"

    # Step 1: Load configuration
    config = load_config(config_path)

    # Step 2: Identify and parse data based on config
    parsed_data = identify_and_parse_data(config)

    # Step 3: Save parsed data to SQLite
    save_to_sqlite(parsed_data, db_path)

    # Step 4: Perform clustering and save results
    for table_name, _ in parsed_data:
        cluster_table_name = f"{table_name}_clusters"
        perform_clustering(db_path, table_name, cluster_table_name)