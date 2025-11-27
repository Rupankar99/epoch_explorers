from .base_model import BaseModel 
import json
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

class RAGHistoryModel(BaseModel):
    """
    Model for rag_history_and_optimization table in optimized schema.
    Unified historical log for queries, healing operations, and synthetic tests.
    """
    
    # --- Class-level Configuration (Adopting BaseModel Structure) ---
    table = 'rag_history_and_optimization'
    fields = [
        'history_id', 'event_type', 'timestamp', 'query_text', 'target_doc_id',
        'target_chunk_id', 'metrics_json', 'context_json', 'reward_signal',
        'action_taken', 'state_before', 'state_after', 'agent_id', 'user_id', 
        'session_id'
    ]
    # NOTE: Assuming BaseModel handles __init__, connection, cursor, execute, and row_factory=sqlite3.Row.
    def get_metrix(self) -> pd.DataFrame:
        """
        Fetch all events from the `rag_history_and_optimization` table as a Pandas DataFrame,
        parsing `metrics_json` and `context_json` into Python dictionaries.
        """
        # Load all rows into a DataFrame
        df = pd.read_sql_query("SELECT * FROM rag_history_and_optimization", self.conn)

        if df.empty:
            return df

        # Parse JSON columns
        df["metrics"] = df["metrics_json"].apply(lambda x: json.loads(x) if x else {})
        df["context"] = df["context_json"].apply(lambda x: json.loads(x) if x else {})

        # Optional: lowercase column names
        df.columns = [c.lower() for c in df.columns]

        return df

    
    def _row_to_dict(self, row) -> Dict | None:
        """Helper to convert sqlite3.Row or tuple to a dictionary based on self.fields."""
        if row is None:
            return None
        
        # If BaseModel uses row_factory=sqlite3.Row (best practice for this type of object)
        if hasattr(row, 'keys'):
            return dict(row)
        
        # Fallback if row is a tuple, relies on the SELECT query order matching self.fields
        return dict(zip(self.fields, row))

    # --- Logging Methods ---

    def log_query(self, query_text: str, target_doc_id: str, 
                  metrics_json: str, context_json: str = None,
                  agent_id: str = "langgraph_agent", user_id: str = None,
                  session_id: str = None) -> int:
        """Log a query event."""
        try:
            now_iso = datetime.now().isoformat()
            
            # Use only the columns needed for this specific insert (fields excluded for QUERY)
            insert_fields = [
                'event_type', 'query_text', 'target_doc_id', 'metrics_json', 
                'context_json', 'timestamp', 'agent_id', 'user_id', 'session_id'
            ]
            columns = ", ".join(insert_fields)
            placeholders = ", ".join(["?"] * len(insert_fields))
            
            data = (
                "QUERY", query_text, target_doc_id, metrics_json, 
                context_json or json.dumps({}), now_iso, agent_id, user_id, session_id
            )

            self.execute(f"""
                INSERT INTO {self.table} ({columns})
                VALUES ({placeholders})
            """, data)
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging query: {e}")
            return -1

    def log_healing(self, target_doc_id: str, target_chunk_id: str,
                    metrics_json: str, context_json: str = None,
                    action_taken: str = None, reward_signal: float = None,
                    agent_id: str = "langgraph_agent", session_id: str = None) -> int:
        """Log a healing/optimization event."""
        try:
            now_iso = datetime.now().isoformat()
            
            insert_fields = [
                'event_type', 'target_doc_id', 'target_chunk_id', 'metrics_json',
                'context_json', 'action_taken', 'reward_signal', 'timestamp',
                'agent_id', 'session_id'
            ]
            columns = ", ".join(insert_fields)
            placeholders = ", ".join(["?"] * len(insert_fields))
            
            data = (
                "HEAL", target_doc_id, target_chunk_id, metrics_json,
                context_json or json.dumps({}), action_taken, reward_signal, now_iso,
                agent_id, session_id
            )

            self.execute(f"""
                INSERT INTO {self.table} ({columns})
                VALUES ({placeholders})
            """, data)
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging healing: {e}")
            return -1

    def log_synthetic_test(self, query_text: str, target_doc_id: str,
                           metrics_json: str, context_json: str = None,
                           agent_id: str = "langgraph_agent", session_id: str = None) -> int:
        """Log a synthetic test event."""
        try:
            now_iso = datetime.now().isoformat()
            
            insert_fields = [
                'event_type', 'query_text', 'target_doc_id', 'metrics_json',
                'context_json', 'timestamp', 'agent_id', 'session_id'
            ]
            columns = ", ".join(insert_fields)
            placeholders = ", ".join(["?"] * len(insert_fields))

            data = (
                "SYNTHETIC_TEST", query_text, target_doc_id, metrics_json,
                context_json or json.dumps({}), now_iso, agent_id, session_id
            )

            self.execute(f"""
                INSERT INTO {self.table} ({columns})
                VALUES ({placeholders})
            """, data)
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging synthetic test: {e}")
            return -1

    # --- Retrieval Methods ---
    
    def get_by_id(self, history_id: int) -> dict | None:
        """Get history record by ID."""
        try:
            fields_str = ', '.join(self.fields)
            cur = self.execute(f"""
                SELECT {fields_str}
                FROM {self.table}
                WHERE history_id = ?
            """, (history_id,))
            
            return self._row_to_dict(cur.fetchone())
            
        except Exception as e:
            print(f"Error getting history record: {e}")
            return None
    
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        """Get history records by event type."""
        try:
            fields_str = ', '.join(self.fields)
            cur = self.execute(f"""
                SELECT {fields_str}
                FROM {self.table}
                WHERE event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (event_type, limit))
            
            return [self._row_to_dict(row) for row in cur.fetchall()]
            
        except Exception as e:
            print(f"Error getting history by event type: {e}")
            return []
    
    def get_by_doc_id(self, doc_id: str, limit: int = 100) -> List[Dict]:
        """Get all history records for a document."""
        try:
            fields_str = ', '.join(self.fields)
            cur = self.execute(f"""
                SELECT {fields_str}
                FROM {self.table}
                WHERE target_doc_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (doc_id, limit))
            
            return [self._row_to_dict(row) for row in cur.fetchall()]
            
        except Exception as e:
            print(f"Error getting history by doc_id: {e}")
            return []
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get all history for a session."""
        try:
            fields_str = ', '.join(self.fields)
            cur = self.execute(f"""
                SELECT {fields_str}
                FROM {self.table}
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            return [self._row_to_dict(row) for row in cur.fetchall()]
            
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
    
    # --- Statistics Method ---

    def get_statistics(self, event_type: str = None) -> Dict[str, Any]:
        """Get statistics about history records (count per event type)."""
        try:
            query = f"""
                SELECT COUNT(*), event_type FROM {self.table}
            """
            params = ()
            
            if event_type:
                query += " WHERE event_type = ?"
                params = (event_type,)
            
            query += " GROUP BY event_type"
                
            cur = self.execute(query, params)
            rows = cur.fetchall()
            
            stats = {"total": 0}
            
            for count, evt_type in rows:
                stats[evt_type] = count
                stats["total"] += count
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
