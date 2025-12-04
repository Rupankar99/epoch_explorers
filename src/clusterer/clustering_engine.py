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
from llm_service import LLMService


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
        
        # Initialize LLM Service for multi-provider support (Azure, OpenAI, Ollama, etc.)
        self.llm_service = None
        self.llm_enabled = False
        self.llm_mode = "RULE_BASED"  # default fallback
        
        try:
            llm_config_path = os.path.join(current_dir, "llm_config.json")
            if os.path.exists(llm_config_path):
                with open(llm_config_path, 'r') as f:
                    llm_config = json.load(f)
                self.llm_service = LLMService(llm_config)
                self.llm_enabled = True
                provider = llm_config.get('default_provider', 'unknown')
                self.llm_mode = f"LLM SERVICE ({provider.upper()})"
                print(f"✓ LLM Service initialized with provider: {provider}")
            else:
                print(f"⚠️ llm_config.json not found at {llm_config_path}, using rule-based explanations")
        except Exception as e:
            print(f"⚠️ Failed to initialize LLM Service: {e}, using rule-based explanations")
        
        self._init_database()
        print(f"[ClusteringEngine] LLM Mode: {self.llm_mode}")
    
    def _init_database(self):
        """Initialize database and create metadata table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Do NOT drop metadata table - preserve clustering history
        # Only create it if it doesn't exist
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
            # Clear old staged tables for re-ingestion
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Only drop staged tables, not final/approved tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", ('%_staged',))
            tables_to_drop = [row[0] for row in cursor.fetchall()]
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
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
    
    def _get_llm_explanation(self, variant_name: str, result: dict, df: pd.DataFrame) -> str:
        """Get LLM-based explanation using LLMService (Azure, OpenAI, Ollama, etc.)"""
        if not self.llm_enabled or not self.llm_service:
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
            
            # Use LLMService to generate response
            response = self.llm_service.generate_response(prompt)
            if response:
                return f"**AI Analysis:**\n\n{response}"
            
        except Exception as e:
            print(f"[LLMService] Error: {e}, falling back to rule-based")
        
        return self._get_rule_based_explanation(variant_name, result, df)
    
    def _get_rule_based_explanation(self, variant_name: str, result: dict, df: pd.DataFrame) -> str:
        """Fallback rule-based explanation (when LLM unavailable)"""
        algorithm = result.get('algorithm', 'unknown')
        silhouette = result.get('silhouette', 0)
        
        text = [f"### {variant_name}\n"]
        
        # Quality assessment with detailed analysis
        if silhouette > 0.7:
            quality = "⭐ EXCELLENT"
            assessment = "Strong and well-separated clusters. Data has clear structure."
        elif silhouette > 0.5:
            quality = "✓ GOOD"
            assessment = "Reasonable cluster structure with acceptable separation."
        elif silhouette > 0.3:
            quality = "◐ FAIR"
            assessment = "Weak cluster separation. Some overlapping between clusters."
        else:
            quality = "✗ POOR"
            assessment = "Poor clustering quality. Clusters are poorly separated or data lacks structure."
        
        text.append(f"**Quality**: {quality}\n")
        text.append(f"**Silhouette Score**: {silhouette:.4f}\n")
        text.append(f"**Assessment**: {assessment}\n\n")
        
        # Algorithm-specific insights
        text.append("**Algorithm Details:**\n")
        if algorithm == 'kmeans':
            k = result.get('k', 0)
            inertia = result.get('inertia', 0)
            text.append(f"- Algorithm: KMeans\n")
            text.append(f"- K (Clusters): {k}\n")
            text.append(f"- Inertia (Sum of squared distances): {inertia:.2f}\n")
            text.append(f"- Insight: {k} clusters found. Lower inertia indicates tighter clusters.\n")
        else:
            eps = result.get('eps', 0)
            n_clusters = result.get('n_clusters', 0)
            n_noise = result.get('n_noise', 0)
            text.append(f"- Algorithm: DBSCAN\n")
            text.append(f"- Eps (Neighborhood radius): {eps}\n")
            text.append(f"- Clusters Found: {n_clusters}\n")
            text.append(f"- Noise Points: {n_noise}\n")
            noise_pct = (n_noise / len(df) * 100) if len(df) > 0 else 0
            text.append(f"- Noise Percentage: {noise_pct:.1f}%\n")
        
        text.append("\n**Recommendations:**\n")
        if silhouette > 0.6:
            text.append("✅ **READY FOR USE** - This clustering provides good quality results.\n")
        elif silhouette > 0.4:
            text.append("⚠️  **TRY ALTERNATIVES** - Consider testing other K values or parameters for potentially better results.\n")
        else:
            text.append("❌ **NOT RECOMMENDED** - Poor quality. Try different parameters or preprocessing techniques.\n")
        
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
                    
                    result['explanation'] = explanation
                    variants[variant_name] = result

                    # Save staged table for this variant
                    if 'labels' in result:
                        if 'k' in result:
                            self._save_staged_table(table_name, df, result['labels'], 'kmeans', 'k', k)
                        elif 'eps' in result:
                            self._save_staged_table(table_name, df, result['labels'], 'dbscan', 'eps', eps)
            
            # DBSCAN variants
            for eps in eps_values:
                result = self._perform_dbscan(df, eps)
                if 'error' not in result:
                    variant_name = f"DBSCAN eps={eps}"
                    
                    # Get LLM explanation
                    explanation = self._get_llm_explanation(variant_name, result, df)
                    
                    # Save metadata
                    self._save_metadata(table_name, variant_name, result, explanation)
                    
                    result['explanation'] = explanation
                    variants[variant_name] = result

                    # Save staged table for this variant
                    if 'labels' in result:
                        if 'eps' in result:
                            self._save_staged_table(table_name, df, result['labels'], 'dbscan', 'eps', eps)
            
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
                # Always write approved results to a unified table
                approved_table = f"{table_name}_pca_approved"
                # If approved table exists, do a merge/update/insert instead of replace
                df_existing = None
                try:
                    df_existing = pd.read_sql_query(f"SELECT * FROM {approved_table}", conn)
                except Exception:
                    pass  # Table does not exist yet
                if cluster_labels:
                    df = pd.read_sql_query(f"SELECT * FROM {staged_table}", conn)
                    df['cluster_label'] = df['cluster'].map(cluster_labels).fillna('Unlabeled')
                    if df_existing is not None:
                        # Merge: update rows with same index, insert new rows
                        df_merged = pd.concat([df_existing, df]).drop_duplicates(subset=df.columns.tolist(), keep='last')
                        df_merged.to_sql(approved_table, conn, if_exists='replace', index=False)
                    else:
                        df.to_sql(approved_table, conn, if_exists='replace', index=False)
                    cursor.execute(f"DROP TABLE IF EXISTS {staged_table}")
                else:
                    df = pd.read_sql_query(f"SELECT * FROM {staged_table}", conn)
                    if df_existing is not None:
                        df_merged = pd.concat([df_existing, df]).drop_duplicates(subset=df.columns.tolist(), keep='last')
                        df_merged.to_sql(approved_table, conn, if_exists='replace', index=False)
                    else:
                        df.to_sql(approved_table, conn, if_exists='replace', index=False)
                    cursor.execute(f"DROP TABLE IF EXISTS {staged_table}")
                # Update metadata status
                cursor.execute(f"UPDATE {self.metadata_table} SET status='approved' WHERE variant_name=? AND table_name=?", (variant_name, table_name))
                # After approving, drop all other staged tables for this table_name except the selected one
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f'{table_name}_%_staged',))
                all_staged = [row[0] for row in cursor.fetchall()]
                for tbl in all_staged:
                    if tbl != staged_table:
                        cursor.execute(f"DROP TABLE IF EXISTS {tbl}")
                conn.commit()
                conn.close()
                return {'status': 'success', 'final_table': approved_table}
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
            print(f"[Engine] ✅ Staged table created: {staged_table}")
            return staged_table
        except Exception as e:
            print(f"[Engine] ❌ Error saving staged table: {e}")
            return None
