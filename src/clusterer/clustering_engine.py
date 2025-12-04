"""
ClusteringEngine - Core clustering execution engine
Handles all business logic: data loading, clustering, LLM, metadata, DB operations
Low-level engine wrapped by agentic orchestrator for intelligent workflow
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path

from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

from data_allocator import load_config, identify_and_parse_data, save_to_sqlite


class ClusteringEngine:
    """
    Core clustering execution engine:
    - Database management
    - Data loading from config
    - Clustering execution (KMeans, DBSCAN)
    - Metadata persistence
    - LLM-based explanations (via Ollama/OpenAI)
    """
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(current_dir, "config.yaml")
        self.db_path = os.path.join(current_dir, "cluster_data.db")
        self.metadata_table = "clustering_metadata"
        
        # LLM Configuration (can be set from environment)
        self.llm_provider = os.getenv('CLUSTERING_LLM_PROVIDER', 'ollama')  # ollama, openai, or none
        self.llm_enabled = False
        self.llm_mode = "RULE_BASED"  # default
        
        self._check_llm_availability()
        self._init_database()
        print(f"[ClusteringEngine] LLM Mode: {self.llm_mode}")
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM is available (Ollama, OpenAI, etc.)"""
        try:
            import requests
            
            if self.llm_provider == 'ollama':
                # Try to connect to Ollama at localhost:11434
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    if models:
                        self.llm_enabled = True
                        self.llm_mode = f"OLLAMA ({models[0]['name']})"
                        print(f"✓ Ollama available with models: {[m['name'] for m in models[:3]]}")
                        return True
            
            elif self.llm_provider == 'openai':
                # Check if OpenAI API key is set
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.llm_enabled = True
                    self.llm_mode = "OPENAI (GPT-3.5/4)"
                    print("✓ OpenAI API key found")
                    return True
        
        except Exception as e:
            pass
        
        print(f"⚠️ No LLM available ({self.llm_provider}), using rule-based explanations")
        return False
    
    def _init_database(self):
        """Initialize database and create metadata table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop old table if exists (schema mismatch fix)
        cursor.execute(f"DROP TABLE IF EXISTS {self.metadata_table}")
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.metadata_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                table_name TEXT NOT NULL,
                variant_name TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                parameters TEXT,
                silhouette_score REAL,
                quality_assessment TEXT,
                llm_explanation TEXT,
                status TEXT DEFAULT 'staged',
                metadata_json TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def run_ingestion(self) -> dict:
        """Run data ingestion from config.yaml"""
        try:
            # Clear old staged/final tables and metadata for re-ingestion
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all staged and final tables from current ingestion
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%_staged' OR name LIKE '%_final')")
            tables_to_drop = [row[0] for row in cursor.fetchall()]
            
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            # Clear old metadata
            cursor.execute(f"DELETE FROM {self.metadata_table}")
            conn.commit()
            conn.close()
            
            config = load_config(self.config_path)
            parsed_data = identify_and_parse_data(config)
            save_to_sqlite(parsed_data, self.db_path)
            
            tables = self.get_tables()
            return {
                'status': 'success',
                'tables_loaded': len(tables),
                'tables': tables
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_tables(self) -> list:
        """Get list of available tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_staged' AND name NOT LIKE '%_final' AND name NOT LIKE '%metadata%'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    def get_table_data(self, table_name: str) -> pd.DataFrame:
        """Get data from table"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    
    def _perform_kmeans(self, df: pd.DataFrame, k: int) -> dict:
        """Execute KMeans clustering"""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {'error': 'No numeric columns'}
        
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df)
        
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled_data)
        silhouette = silhouette_score(scaled_data, labels)
        
        return {
            'algorithm': 'kmeans',
            'k': k,
            'labels': labels.tolist(),
            'silhouette': silhouette,
            'inertia': kmeans.inertia_,
            'parameters': {'k': k}
        }
    
    def _perform_dbscan(self, df: pd.DataFrame, eps: float) -> dict:
        """Execute DBSCAN clustering"""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {'error': 'No numeric columns'}
        
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_df)
        
        dbscan = DBSCAN(eps=eps, min_samples=5)
        labels = dbscan.fit_predict(scaled_data)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        silhouette = silhouette_score(scaled_data, labels) if n_clusters > 1 else -1
        
        return {
            'algorithm': 'dbscan',
            'eps': eps,
            'labels': labels.tolist(),
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'silhouette': silhouette,
            'parameters': {'eps': eps, 'min_samples': 5}
        }
    
    def _save_metadata(self, table_name: str, variant_name: str, result: dict, explanation: str = ""):
        """Save clustering metadata to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                INSERT INTO {self.metadata_table} 
                (timestamp, table_name, variant_name, algorithm, parameters, silhouette_score, llm_explanation, metadata_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'staged')
            """, (
                datetime.now().isoformat(),
                table_name,
                variant_name,
                result.get('algorithm', 'unknown'),
                json.dumps(result.get('parameters', {})),
                result.get('silhouette', 0),
                explanation,
                json.dumps(result)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
    
    def _save_staged_table(self, table_name: str, df: pd.DataFrame, labels: list, algorithm: str, param_name: str, param_value):
        """Save clustering results to staged table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            df_with_clusters = df.copy()
            df_with_clusters['cluster'] = labels
            
            # Staged table name format: tablename_algorithm_paramvalue_staged
            # Use safe float formatting: 0.3 -> 0p3, 0.5 -> 0p5, 1.0 -> 1p0
            if isinstance(param_value, float):
                param_str = f"{param_value:.1f}".replace('.', 'p')
            else:
                param_str = str(param_value)
            
            staged_table = f"{table_name}_{algorithm}_{param_name}{param_str}_staged"
            
            # Drop if exists to handle re-ingestion gracefully
            cursor.execute(f"DROP TABLE IF EXISTS {staged_table}")
            conn.commit()
            
            # Create table if not exists and insert data
            df_with_clusters.to_sql(staged_table, conn, if_exists='replace', index=False)
            
            conn.close()
            return staged_table
        except Exception as e:
            print(f"Error saving staged table: {e}")
            return None
    
    def _get_llm_explanation(self, variant_name: str, result: dict, df: pd.DataFrame) -> str:
        """Get LLM-based explanation using Ollama/OpenAI/local LLM"""
        if not self.llm_enabled:
            return self._get_rule_based_explanation(variant_name, result, df)
        
        try:
            # Build analysis prompt
            algorithm = result.get('algorithm', 'unknown')
            metrics_text = f"""
Algorithm: {algorithm.upper()}
Silhouette Score: {result.get('silhouette', 0):.4f}
"""
            if algorithm == 'kmeans':
                metrics_text += f"K Value: {result.get('k', 0)}\nInertia: {result.get('inertia', 0):.2f}"
            else:
                metrics_text += f"Eps: {result.get('eps', 0)}\nClusters Found: {result.get('n_clusters', 0)}\nNoise Points: {result.get('n_noise', 0)}"
            
            prompt = f"""Analyze this clustering result and provide insights:
{metrics_text}

Data shape: {df.shape}
Columns: {', '.join(df.columns.tolist())}

Provide a brief analysis of the clustering quality, what it means, and recommendations."""
            
            if self.llm_provider == 'ollama':
                return self._get_ollama_explanation(prompt)
            elif self.llm_provider == 'openai':
                return self._get_openai_explanation(prompt)
            
        except Exception as e:
            print(f"LLM error: {e}, falling back to rule-based")
        
        return self._get_rule_based_explanation(variant_name, result, df)
    
    def _get_ollama_explanation(self, prompt: str) -> str:
        """Get explanation from local Ollama instance"""
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama2", "prompt": prompt, "stream": False},
                timeout=10
            )
            
            if response.status_code == 200:
                text = response.json().get('response', '')
                return f"**AI Analysis (Ollama):**\n\n{text}"
        
        except Exception as e:
            print(f"Ollama error: {e}")
        
        return None
    
    def _get_openai_explanation(self, prompt: str) -> str:
        """Get explanation from OpenAI API"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("OPENAI_API_KEY not set")
                return None
            
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            text = response['choices'][0]['message']['content']
            return f"**AI Analysis (OpenAI GPT-3.5):**\n\n{text}"
        
        except Exception as e:
            print(f"OpenAI error: {e}")
        
        return None
    
    def _get_rule_based_explanation(self, variant_name: str, result: dict, df: pd.DataFrame) -> str:
        """Fallback rule-based explanation (when LLM unavailable)"""
        algorithm = result.get('algorithm', 'unknown')
        silhouette = result.get('silhouette', 0)
        
        text = [f"## {variant_name}\n**Algorithm**: {algorithm.upper()}\n"]
        
        # Quality assessment
        if silhouette > 0.7:
            quality = "EXCELLENT ✅ - Strong cluster separation"
        elif silhouette > 0.5:
            quality = "GOOD ✅ - Reasonable cluster structure"
        elif silhouette > 0.3:
            quality = "FAIR ⚠️ - Weak cluster separation"
        else:
            quality = "POOR ❌ - Consider different parameters"
        
        text.append(f"**Silhouette Score**: {silhouette:.4f}\n**Quality**: {quality}\n")
        
        # Metrics details
        text.append("### Metrics:\n")
        if algorithm == 'kmeans':
            text.append(f"- K: {result.get('k', 0)}\n")
            text.append(f"- Inertia: {result.get('inertia', 0):.2f}\n")
        else:
            text.append(f"- Eps: {result.get('eps', 0)}\n")
            text.append(f"- Clusters: {result.get('n_clusters', 0)}\n")
            text.append(f"- Noise: {result.get('n_noise', 0)}\n")
        
        # Recommendations
        text.append("\n### Recommendations:\n")
        if silhouette > 0.5:
            text.append("✅ This clustering is of good quality and ready for production use.\n")
        elif silhouette > 0.3:
            text.append("⚠️ Moderate quality - consider trying other parameter values.\n")
        else:
            text.append("❌ Poor quality - try different K values or preprocessing.\n")
        
        return "".join(text)
    
    def run_clustering(self, table_name: str, k_values: list, eps_values: list = None) -> dict:
        """Run clustering with multiple K values and algorithms"""
        try:
            df = self.get_table_data(table_name)
            variants = {}
            
            # Set default eps values if not provided
            if eps_values is None:
                eps_values = [0.3, 0.5, 0.7]
            
            # KMeans variants
            for k in k_values:
                result = self._perform_kmeans(df, k)
                if 'error' not in result:
                    variant_name = f"KMeans K={k}"
                    
                    # Get LLM explanation
                    explanation = self._get_llm_explanation(variant_name, result, df)
                    
                    # Save metadata
                    self._save_metadata(table_name, variant_name, result, explanation)
                    
                    # Save staged table
                    self._save_staged_table(table_name, df, result['labels'], 'kmeans', 'k', k)
                    
                    result['explanation'] = explanation
                    variants[variant_name] = result
            
            # DBSCAN variants
            for eps in eps_values:
                result = self._perform_dbscan(df, eps)
                if 'error' not in result:
                    variant_name = f"DBSCAN eps={eps}"
                    
                    # Get LLM explanation
                    explanation = self._get_llm_explanation(variant_name, result, df)
                    
                    # Save metadata
                    self._save_metadata(table_name, variant_name, result, explanation)
                    
                    # Save staged table
                    self._save_staged_table(table_name, df, result['labels'], 'dbscan', 'eps', eps)
                    
                    result['explanation'] = explanation
                    variants[variant_name] = result
            
            return {'status': 'success', 'variants': variants}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_clustering_explanation(self, variant_name: str, variant_data: dict, df: pd.DataFrame) -> str:
        """Get explanation for a clustering variant"""
        if 'explanation' in variant_data:
            return variant_data['explanation']
        return self._get_llm_explanation(variant_name, variant_data, df)
    
    def approve_and_save(self, table_name: str, variant_name: str, variant_data: dict, cluster_labels: dict = None) -> dict:
        """
        Approve clustering and move from staged to final
        cluster_labels: dict mapping cluster_id -> label_name
        Example: {0: 'High Risk', 1: 'Medium Risk', 2: 'Low Risk'}
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find staged table
            algorithm = variant_data.get('algorithm', 'kmeans')
            if algorithm == 'kmeans':
                k = variant_data.get('k')
                staged_pattern = f"{table_name}_kmeans_k{k}_staged"
            else:
                eps = variant_data.get('eps')
                # Handle float precision: use p instead of . to avoid SQL issues
                # 0.3 -> 0p3, 0.5 -> 0p5, 1.0 -> 1p0
                eps_str = f"{eps:.1f}".replace('.', 'p')
                staged_pattern = f"{table_name}_dbscan_eps{eps_str}_staged"
            
            # Search for the staged table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (staged_pattern,))
            result = cursor.fetchone()
            
            if not result:
                # Fallback: search for any staged table with similar pattern
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                    (f"{table_name}_{algorithm}%_staged",)
                )
                result = cursor.fetchone()
                if result:
                    print(f"[Approval] Found staged table: {result[0]} (pattern was: {staged_pattern})")
            
            if result:
                staged_table = result[0]
                final_table = staged_table.replace("_staged", "_final")
                
                # If cluster labels provided, add label column
                if cluster_labels:
                    # Read staged data
                    df = pd.read_sql_query(f"SELECT * FROM {staged_table}", conn)
                    df['cluster_label'] = df['cluster'].map(cluster_labels).fillna('Unlabeled')
                    
                    # Truncate (delete if exists) and recreate final table with if_exists='replace'
                    # This handles re-ingestion scenarios gracefully
                    if_exists = 'replace'
                    df.to_sql(final_table, conn, if_exists=if_exists, index=False)
                    cursor.execute(f"DROP TABLE IF EXISTS {staged_table}")
                else:
                    # No labels - read staged, write to final table with CREATE TABLE IF NOT EXISTS
                    df = pd.read_sql_query(f"SELECT * FROM {staged_table}", conn)
                    
                    if_exists = 'replace'  # This truncates and recreates
                    df.to_sql(final_table, conn, if_exists=if_exists, index=False)
                    cursor.execute(f"DROP TABLE IF EXISTS {staged_table}")
                
                # Update metadata status
                cursor.execute(f"UPDATE {self.metadata_table} SET status='approved' WHERE variant_name=? AND table_name=?", (variant_name, table_name))
                
                conn.commit()
                conn.close()
                
                return {'status': 'success', 'final_table': final_table}
            else:
                # Better error message - list available staged tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f"{table_name}%_staged",))
                available_tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                error_msg = f"Staged table not found. Searched for: {staged_pattern}"
                if available_tables:
                    error_msg += f". Available: {', '.join(available_tables)}"
                print(f"[Approval Error] {error_msg}")
                return {'status': 'error', 'error': error_msg}
        except Exception as e:
            print(f"[Approval Exception] {str(e)}")
            return {'status': 'error', 'error': str(e)}
