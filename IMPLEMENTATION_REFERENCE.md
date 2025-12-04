# Complete Implementation Reference

## System Architecture

The enhanced clustering pipeline implements a modular, configurable workflow for multi-source data ingestion, multi-algorithm clustering, and human-approved cluster selection.

## Core Components

### 1. Configuration Layer (`config.yaml`)

**Purpose**: Define data sources without hardcoding

```yaml
data_sources:
  - path: "data/input"          # Directory path
    file_name: "*.csv"          # File pattern (wildcard support)
  - path: "data/json"
    file_name: "*.json"
  - path: "data/all"
    file_name: "*"              # All files in directory
```

**Supported File Types**:
- CSV (`.csv`)
- JSON (`.json`)
- Any text-based format via pattern

### 2. Data Allocator (`data_allocator.py`)

**Functions**:

```python
def load_config(config_path: str) -> dict:
    """Load YAML configuration file"""
    # Returns: {'data_sources': [...]}

def identify_and_parse_data(config: dict) -> List[Tuple[str, pd.DataFrame]]:
    """Parse files matching config patterns"""
    # Returns: [('table_name', DataFrame), ...]

def save_to_sqlite(parsed_data: list, db_path: str):
    """Save DataFrames to SQLite with auto-schema"""
    # Creates tables with auto-detected types

def auto_detect_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Detect column types automatically"""
    # Returns: {'col_name': 'INTEGER|REAL|TEXT|BOOLEAN'}

def get_dataframe_info(df: pd.DataFrame) -> Dict:
    """Get comprehensive DataFrame metadata"""
    # Returns: rows, columns, dtypes, schema, etc.
```

### 3. Clustering Algorithms

#### KMeans Clustering

```python
def perform_kmeans_clustering(df: pd.DataFrame, k: int) -> dict:
    """
    Perform KMeans clustering
    
    Args:
        df: Input DataFrame
        k: Number of clusters
    
    Returns:
        {
            'algorithm': 'kmeans',
            'k': k,
            'labels': [...],           # Cluster assignments
            'silhouette': 0.65,        # Quality score
            'inertia': 123.45,         # Inertia value
            'centers': [...]           # Cluster centers
        }
    """
    # 1. Select numeric columns
    # 2. Standardize data
    # 3. Fit KMeans
    # 4. Calculate metrics
```

#### DBSCAN Clustering

```python
def perform_dbscan_clustering(
    df: pd.DataFrame, 
    eps: float = 0.5, 
    min_samples: int = 5
) -> dict:
    """
    Perform DBSCAN clustering
    
    Args:
        df: Input DataFrame
        eps: Epsilon parameter (neighborhood radius)
        min_samples: Minimum samples in neighborhood
    
    Returns:
        {
            'algorithm': 'dbscan',
            'eps': eps,
            'min_samples': min_samples,
            'labels': [...],           # Cluster assignments
            'n_clusters': 5,           # Number of clusters found
            'n_noise': 2,              # Number of noise points
            'silhouette': 0.42         # Quality score
        }
    """
```

### 4. LangGraph Orchestrator (`langgraph_orchestrator.py`)

#### Initialization

```python
from langgraph_orchestrator import LangGraphDataPipeline

pipeline = LangGraphDataPipeline(
    config_path="src/clusterer/config.yaml",      # Config file
    db_path="src/clusterer/cluster_data.db",      # SQLite path
    use_case="customer_segmentation",             # Use case
    domain_context="e-commerce",                  # Domain
    hitl_enabled=True,                            # Enable approval
    verbose=True,                                 # Enable logging
    k_values=[3, 5, 8]                           # K values for KMeans
)
```

#### Pipeline Nodes

**1. DataAllocation Node**

```python
def _node_data_allocation(self, state: GraphState) -> Dict:
    """
    Load config and ingest multi-source data
    
    Inputs: config_path, db_path
    Outputs: 
        - parsed_data: List of (table_name, DataFrame)
        - data_loaded: bool
        - db_path: Connection string
    """
```

**2. Clustering Node**

```python
def _node_clustering(self, state: GraphState) -> Dict:
    """
    Generate clustering variants
    
    For each table in SQLite:
        For each K in k_values:
            - Run KMeans
            - Save to {table}_kmeans_k{k}_staged
        For each eps in [0.3, 0.5, 0.7]:
            - Run DBSCAN
            - Save to {table}_dbscan_eps{eps}_staged
    
    Outputs:
        - clustering_variants: Dict of all variants
        - clustering_analysis: LLM analysis text
    """
```

**3. LLM Analysis Node**

```python
def _node_llm_analysis(self, state: GraphState) -> Dict:
    """
    Analyze clustering variability
    
    Compares silhouette scores and provides insights
    Output format:
        "KMeans (K=5): Silhouette=0.65, Inertia=120.45
         Quality: Excellent
         DBSCAN (eps=0.5): Found 8 clusters..."
    """
```

**4. HITL Approval Node**

```python
def _node_hitl_clustering_approval(self, state: GraphState) -> Dict:
    """
    Wait for user to select variant
    
    Returns:
        - hitl_approval: None (waiting) or bool (decided)
        - approved_clustering_config: {algorithm, k, eps}
    """
```

**5. SaveFinal Node**

```python
def _node_save_final_clusters(self, state: GraphState) -> Dict:
    """
    Rename staged → final tables
    
    Logic:
        1. Get approved_clustering_config
        2. Find matching staged table
        3. Rename to final table
        4. Create audit record
    
    Example:
        customers_kmeans_k5_staged → customers_kmeans_k5_final
    """
```

#### Execution

```python
import asyncio

async def run_pipeline():
    state = await pipeline.run(
        input_data={},
        user_query="Segment customers",
        session_id="session_001"
    )
    
    return state

result = asyncio.run(run_pipeline())
```

### 5. Streamlit Dashboard (`dashboard_enhanced.py`)

#### Page: Ingestion

```python
def ingest_data() -> bool:
    """
    Load config, parse files, save to SQLite
    
    1. load_config(CONFIG_PATH)
    2. identify_and_parse_data(config)
    3. save_to_sqlite(parsed_data, DB_PATH)
    
    Returns: Success boolean
    """
```

#### Page: Clustering

```python
def perform_clustering_variants(
    table_name: str, 
    df: pd.DataFrame, 
    k_values: List[int]
) -> Dict:
    """
    Generate variants and save staged tables
    
    For each K in k_values:
        - Run KMeans
        - Save to {table}_kmeans_k{K}_staged
    
    For each eps in [0.3, 0.5, 0.7]:
        - Run DBSCAN
        - Save to {table}_dbscan_eps{eps}_staged
    
    Returns:
        {
            'KMeans K=3': {silhouette, labels, ...},
            'KMeans K=5': {...},
            'DBSCAN eps=0.3': {...},
            ...
        }
    """
```

#### Page: Approval

```python
def approve_clustering(selected_variant: Dict) -> bool:
    """
    Rename selected staged table to final
    
    1. Extract algorithm + params from variant
    2. Find matching staged table
    3. Rename to {table}_{algo}_{param}_final
    
    Returns: Success boolean
    """
```

## State Management

### GraphState TypedDict

```python
class GraphState(TypedDict):
    # Session
    session_id: str
    pipeline_id: str
    config_path: str
    db_path: str
    
    # Data
    raw_data: Dict
    parsed_data: List[Tuple]
    
    # Clustering
    clustering_variants: Dict      # All generated variants
    selected_clustering: Dict      # User selected variant
    approved_clustering_config: Dict
    
    # Approval
    hitl_approval: Optional[bool]  # None=waiting, True/False=decided
    human_approved: bool           # Final status
    
    # Status
    current_stage: str
    data_loaded: bool
    
    # Audit
    execution_log: List[Dict]
    timestamps: Dict[str, str]
    errors: List[str]
```

## Table Naming Convention

### Base Table (Ingestion)

```
{filename}
Example: customers, transactions, products
```

### Staged Tables (Clustering Variants)

```
KMeans:
  {table}_kmeans_k{K}_staged
  Example: customers_kmeans_k3_staged
           customers_kmeans_k5_staged
           customers_kmeans_k8_staged

DBSCAN:
  {table}_dbscan_eps{eps}_staged
  Example: customers_dbscan_eps0.3_staged
           customers_dbscan_eps0.5_staged
           customers_dbscan_eps0.7_staged
```

### Final Table (Approved)

```
{table}_{algorithm}_{param}_final
Example: customers_kmeans_k5_final
         products_dbscan_eps0.5_final
```

## Schema Auto-Detection

```python
Type Detection Logic:
  int64, int32          → INTEGER
  float64, float32      → REAL
  bool                  → BOOLEAN
  object, string, etc   → TEXT

Example:
  Input DataFrame:
    age (int64)        → age INTEGER
    salary (float64)   → salary REAL
    name (object)      → name TEXT
    active (bool)      → active BOOLEAN
```

## Data Flow Examples

### Example 1: Simple CSV Clustering

```yaml
# config.yaml
data_sources:
  - path: "data/customers"
    file_name: "*.csv"
```

```
Flow:
  1. DataAllocation: Load customers.csv
  2. Clustering: Generate KMeans (K=3,5,8) + DBSCAN (eps=0.3,0.5,0.7)
  3. LLM Analysis: Compare 6 variants
  4. HITL Approval: User selects best (e.g., KMeans K=5)
  5. SaveFinal: Create customers_kmeans_k5_final
```

### Example 2: Multi-Source JSON+CSV

```yaml
# config.yaml
data_sources:
  - path: "data/customers_csv"
    file_name: "*.csv"
  - path: "data/customer_json"
    file_name: "*.json"
```

```
Flow:
  1. DataAllocation: Load all CSV + JSON files into separate tables
  2. Clustering: For each table, generate variants
     - customers_csv → customers_kmeans_k5_staged
     - customer_json → customer_kmeans_k5_staged
  3. Dashboard: User selects table and clustering variant
  4. SaveFinal: Create final table with approved clustering
```

## API Reference

### Public Methods

```python
# Main execution
await pipeline.run(
    input_data: Dict = {},
    user_query: str = "",
    session_id: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> GraphState

# Get table list
get_tables() -> List[str]

# Load data
load_config(config_path: str) -> Dict
identify_and_parse_data(config: Dict) -> List[Tuple[str, DataFrame]]
save_to_sqlite(parsed_data: List, db_path: str) -> None

# Clustering
perform_kmeans_clustering(df: DataFrame, k: int) -> Dict
perform_dbscan_clustering(df: DataFrame, eps: float, min_samples: int) -> Dict

# Analysis
analyze_clustering_variability_with_llm(variants: Dict) -> str
auto_detect_schema(df: DataFrame) -> Dict[str, str]
```

## Error Handling

```python
try:
    pipeline = LangGraphDataPipeline(config_path="config.yaml")
    result = await pipeline.run({})
except FileNotFoundError:
    print("Config or database not found")
except ValueError:
    print("Invalid configuration or data")
except Exception as e:
    print(f"Pipeline error: {str(e)}")
```

## Performance Considerations

- **Large Files**: Staged tables created for each variant (uses disk space)
- **Many K Values**: Linear time increase with K count
- **DBSCAN eps**: Three fixed values tested (0.3, 0.5, 0.7)
- **Schema Detection**: O(rows) for type inference
- **Silhouette Score**: O(n²) complexity for large datasets

## Future Enhancements

- [ ] Distributed clustering for large datasets
- [ ] Custom distance metrics
- [ ] Clustering validation metrics
- [ ] Automated K selection via elbow method
- [ ] Real LLM integration with model API
- [ ] Cluster visualization/plotting
- [ ] Batch pipeline execution
- [ ] Historical approval tracking
