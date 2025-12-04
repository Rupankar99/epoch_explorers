"""
🤖 AI-Powered Data Clustering Dashboard - v2
- Unified Ingestion + Clustering workflow
- Config-driven clustering with UI override capability
- Auto-triggered clustering on page load
- LangGraph agentic orchestration with LLM analysis
"""

import streamlit as st
import json
import os
import sqlite3
import yaml
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from agentic_orchestrator import AgenticClusteringOrchestrator

# ========================
# PAGE CONFIGURATION
# ========================

st.set_page_config(
    page_title="🤖 AI Clustering Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 AI-Powered Data Clustering Dashboard")
st.markdown("*Agentic LangGraph Workflow with Multi-Provider LLM*")

# ========================
# INITIALIZE ORCHESTRATOR
# ========================

@st.cache_resource
def get_agentic_orchestrator():
    """Get LangGraph-based agentic orchestrator with multi-provider LLM"""
    return AgenticClusteringOrchestrator()

agentic_orch = get_agentic_orchestrator()

class OrchestratorHelper:
    """Helper to access basic orchestrator functions"""
    def __init__(self, agentic_orch):
        self.agentic = agentic_orch
        self.basic = agentic_orch.agent.orchestrator
    
    def run_ingestion(self):
        return self.basic.run_ingestion()
    
    def get_tables(self):
        return self.basic.get_tables()
    
    def get_table_data(self, table_name):
        return self.basic.get_table_data(table_name)

orchestrator = OrchestratorHelper(agentic_orch)

# ========================
# CLUSTERING CONFIG
# ========================

DEFAULT_CLUSTERING_CONFIG = {
    "k_values": [2, 3, 5, 7],
    "eps_values": [0.3, 0.5, 0.7, 1.0],
    "auto_run": True,
    "quality_threshold": 0.5,
    "use_ollama": True
}

def load_clustering_config():
    """Load clustering config from session state or file"""
    if 'clustering_config' not in st.session_state:
        st.session_state.clustering_config = DEFAULT_CLUSTERING_CONFIG.copy()
    return st.session_state.clustering_config

def save_clustering_config(config):
    """Save config to session state"""
    st.session_state.clustering_config = config

# ========================
# DATA SOURCE CONFIG
# ========================

def get_config_path():
    """Get path to config.yaml"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "config.yaml")

def load_data_sources():
    """Load data sources from config.yaml"""
    try:
        config_path = get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('data_sources', [])
        return []
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return []

def save_data_sources(data_sources):
    """Save data sources to config.yaml"""
    try:
        config_path = get_config_path()
        config = {'data_sources': data_sources}
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

# ========================
# VISUALIZATION HELPERS
# ========================

def plot_3d_clustering(df: pd.DataFrame, labels, title: str):
    """Create 3D visualization"""
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        st.error("No numeric columns for visualization")
        return None
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_df)
    
    pca = PCA(n_components=3)
    pca_data = pca.fit_transform(scaled_data)
    
    fig = go.Figure(data=[go.Scatter3d(
        x=pca_data[:, 0],
        y=pca_data[:, 1],
        z=pca_data[:, 2],
        mode='markers',
        marker=dict(
            size=6,
            color=labels,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Cluster"),
            line=dict(width=0.5, color='white')
        ),
        text=[f"Cluster: {l}" for l in labels],
        hovertemplate='%{text}<extra></extra>'
    )])
    
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]:.1%})",
            yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]:.1%})",
            zaxis_title=f"PC3 ({pca.explained_variance_ratio_[2]:.1%})"
        ),
        height=500
    )
    
    return fig

def plot_2d_clustering(df: pd.DataFrame, labels, title: str):
    """Create 2D PCA visualization"""
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        st.error("No numeric columns")
        return None
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_df)
    
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(scaled_data)
    
    fig = go.Figure(data=[go.Scatter(
        x=pca_data[:, 0],
        y=pca_data[:, 1],
        mode='markers',
        marker=dict(
            size=8,
            color=labels,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Cluster"),
            line=dict(width=0.5, color='white')
        ),
        text=[f"Cluster: {l}" for l in labels],
        hovertemplate='PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>%{text}<extra></extra>'
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]:.1%})",
        yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]:.1%})",
        height=400
    )
    
    return fig

def plot_3d_clustering(df: pd.DataFrame, labels, title: str):
    """Create static 3D PCA visualization"""
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        st.error("No numeric columns for visualization")
        return None
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_df)
    
    pca = PCA(n_components=3)
    pca_data = pca.fit_transform(scaled_data)
    
    fig = go.Figure(
        data=[go.Scatter3d(
            x=pca_data[:, 0],
            y=pca_data[:, 1],
            z=pca_data[:, 2],
            mode='markers',
            marker=dict(
                size=6,
                color=labels,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Cluster"),
                line=dict(width=0.5, color='white')
            ),
            text=[f"Cluster: {l}" for l in labels],
            hovertemplate='<b>%{text}</b><extra></extra>'
        )]
    )
    
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]:.1%})",
            yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]:.1%})",
            zaxis_title=f"PC3 ({pca.explained_variance_ratio_[2]:.1%})",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3)
            )
        ),
        height=600,
        showlegend=False,
        hovermode='closest'
    )
    
    return fig

def get_clustering_metadata(orchestrator, table_name: str) -> dict:
    """Get clustering metadata for a table"""
    try:
        conn = sqlite3.connect(orchestrator.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT variant_name, algorithm, parameters, silhouette_score, status FROM clustering_metadata WHERE table_name=?",
            (table_name,)
        )
        results = cursor.fetchall()
        conn.close()
        return {
            'total_variants': len(results),
            'approved_variants': len([r for r in results if r[4] == 'approved']),
            'staged_variants': len([r for r in results if r[4] == 'staged']),
            'variants': results
        }
    except Exception as e:
        return {'error': str(e), 'total_variants': 0}

def plot_cluster_distribution(labels, title: str):
    """Create cluster distribution chart"""
    unique, counts = np.unique(labels, return_counts=True)
    
    fig = go.Figure(data=[go.Bar(
        x=[f"Cluster {c}" if c != -1 else "Noise" for c in unique],
        y=counts,
        marker=dict(color=unique, colorscale='Viridis')
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="Cluster",
        yaxis_title="Count",
        height=300
    )
    
    return fig

# ========================
# MAIN WORKFLOW
# ========================

def main():
    """Main dashboard workflow"""
    
    # Sidebar: Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        config = load_clustering_config()
        
        st.subheader("🔧 Clustering Parameters")
        
        # K values configuration
        st.write("**KMeans K Values:**")
        k_input = st.text_input(
            "Enter K values (comma-separated)",
            value=",".join(map(str, config["k_values"])),
            help="e.g., 2,3,5,7,10"
        )
        try:
            k_values = [int(k.strip()) for k in k_input.split(",") if k.strip()]
            config["k_values"] = k_values
        except ValueError:
            st.error("Invalid K values format")
        
        # Eps values configuration
        st.write("**DBSCAN Eps Values:**")
        eps_input = st.text_input(
            "Enter eps values (comma-separated)",
            value=",".join(map(str, config["eps_values"])),
            help="e.g., 0.3,0.5,0.7,1.0"
        )
        try:
            eps_values = [float(e.strip()) for e in eps_input.split(",") if e.strip()]
            config["eps_values"] = eps_values
        except ValueError:
            st.error("Invalid eps values format")
        
        # Quality threshold
        config["quality_threshold"] = st.slider(
            "Quality Threshold (Silhouette)",
            min_value=0.0,
            max_value=1.0,
            value=config["quality_threshold"],
            step=0.1
        )
        
        # Auto-run toggle
        config["auto_run"] = st.checkbox(
            "Auto-run clustering on load",
            value=config["auto_run"]
        )
        
        save_clustering_config(config)
        
        st.divider()
        
        # LLM Info
        if agentic_orch.agent.llm_service:
            st.subheader("🧠 LLM Status")
            st.info(f"**Provider:** {agentic_orch.agent.llm_service.provider}")
        else:
            st.warning("⚠️ LLM Service not available")
    
    # Main content: Ingestion + Clustering
    st.header("📥 Data Ingestion & 🔍 Clustering")
    
    # Step 1: Data Source Configuration
    st.subheader("Step 1️⃣: Configure Data Sources")
    
    with st.expander("📋 Data Sources Configuration", expanded=True):
        st.write("**Current Data Sources in config.yaml:**")
        
        data_sources = load_data_sources()
        
        # Display current sources
        if data_sources:
            for i, source in enumerate(data_sources):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Path {i+1}:** {source.get('path', 'N/A')}")
                with col2:
                    st.write(f"**Pattern:** {source.get('file_name', '*.csv')}")
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{i}"):
                        data_sources.pop(i)
                        save_data_sources(data_sources)
                        st.rerun()
        else:
            st.info("No data sources configured")
        
        st.divider()
        
        # Add new data source
        st.write("**Add New Data Source:**")
        col1, col2 = st.columns(2)
        with col1:
            new_path = st.text_input(
                "Path to data folder",
                placeholder="e.g., E:/epoch_explorers/src/clusterer/data/transactions",
                key="new_path"
            )
        with col2:
            new_pattern = st.text_input(
                "File pattern",
                value="*.csv",
                placeholder="e.g., *.csv, *.json",
                key="new_pattern"
            )
        
        if st.button("➕ Add Data Source"):
            if new_path:
                data_sources.append({
                    "path": new_path,
                    "file_name": new_pattern
                })
                save_data_sources(data_sources)
                st.success("✓ Data source added!")
                st.rerun()
            else:
                st.error("Please enter a path")
    
    # Step 2: Load Data
    st.divider()
    st.subheader("Step 2️⃣: Load Data from Sources")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Load data using configured sources")
    
    with col2:
        ingest_btn = st.button("📥 Load Data", type="primary")
    
    # Handle ingestion
    if ingest_btn or 'ingestion_done' not in st.session_state:
        with st.spinner("Loading data..."):
            try:
                result = orchestrator.run_ingestion()
                if result['status'] == 'success':
                    st.session_state.ingestion_done = True
                    st.session_state.tables = result.get('tables', [])
                    st.success(f"✓ Ingested {result.get('tables_loaded', 0)} tables")
                else:
                    st.error(f"Ingestion failed: {result.get('error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.get('ingestion_done'):
        st.divider()
        st.subheader("Step 3️⃣: Run Autonomous Clustering")
        
        # Table selection
        tables = st.session_state.get('tables', [])
        if tables:
            selected_table = st.selectbox("📊 Select table to cluster:", tables)
            
            # Show clustering metadata for selected table
            meta = get_clustering_metadata(orchestrator, selected_table)
            if meta.get('total_variants', 0) > 0:
                st.info(f"📊 **Previous Clustering:** {meta['total_variants']} variants | Approved: {meta['approved_variants']} | Staged: {meta['staged_variants']}")
            
            # Get table info
            try:
                df = orchestrator.get_table_data(selected_table)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                    st.metric("Numeric Columns", numeric_cols)
                
                # Auto-run or manual trigger
                config = load_clustering_config()
                should_run = False
                
                if config["auto_run"] and 'auto_clustering_triggered' not in st.session_state:
                    st.session_state.auto_clustering_triggered = True
                    should_run = True
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write("Run autonomous clustering with configured parameters")
                with col2:
                    if st.button("🤖 Run Clustering", type="secondary"):
                        should_run = True
                
                # Execute clustering
                if should_run:
                    with st.spinner("🤖 Agent analyzing clustering options..."):
                        try:
                            workflow_state = agentic_orch.run_autonomous_clustering(
                                table_name=selected_table,
                                custom_k_values=config["k_values"],
                                custom_eps_values=config["eps_values"],
                                quality_threshold=config["quality_threshold"]
                            )
                            
                            st.session_state.workflow_state = workflow_state
                            st.session_state.selected_table = selected_table
                            st.session_state.df = df
                            
                            if workflow_state.get('workflow_status') in ['ready_for_approval', 'awaiting_approval', 'ready_for_review']:
                                st.success("✓ Clustering complete! Variants generated.")
                            elif workflow_state.get('workflow_status') == 'error':
                                error_msg = workflow_state.get('error_message', 'Unknown error')
                                st.error(f"Clustering failed: {error_msg}")
                            else:
                                st.warning(f"Workflow status: {workflow_state.get('workflow_status')}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # Display results if available
                if 'workflow_state' in st.session_state:
                    st.divider()
                    st.header("📊 Results & Analysis")
                    
                    workflow_state = st.session_state.workflow_state
                    variants = workflow_state.get('clustering_variants', {})
                    best_variant = workflow_state.get('best_variant', '')
                    best_quality = workflow_state.get('best_quality', 0)
                    quality_assessment = workflow_state.get('quality_assessment', {})
                    
                    if variants:
                        # Agent recommendations
                        st.subheader("🏆 Agent's Top Recommendation")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Recommended Variant", best_variant)
                        with col2:
                            st.metric("Quality Score", f"{best_quality:.2f}/1.0")
                        with col3:
                            if best_quality > 0.7:
                                st.metric("Status", "✅ EXCELLENT")
                            elif best_quality > 0.5:
                                st.metric("Status", "✅ GOOD")
                            elif best_quality > 0.3:
                                st.metric("Status", "⚠️ FAIR")
                            else:
                                st.metric("Status", "❌ POOR")
                        
                        # Quality ranking
                        st.subheader("📈 Quality Assessment (Ranked)")
                        ranking = sorted(
                            quality_assessment.items(),
                            key=lambda x: x[1]['score'],
                            reverse=True
                        )
                        
                        ranking_data = []
                        for name, assessment in ranking:
                            ranking_data.append({
                                '🏆': '⭐' if name == best_variant else '',
                                'Variant': name,
                                'Silhouette': f"{assessment['silhouette']:.4f}",
                                'Quality': assessment['quality'],
                                'Score': f"{assessment['score']:.2f}"
                            })
                        
                        st.dataframe(pd.DataFrame(ranking_data), width='stretch')
                        
                        # All variants display (horizontal grid)
                        st.subheader("🔍 All Clustering Variants")
                        
                        variant_list = list(variants.items())
                        n_cols = min(4, len(variant_list))
                        
                        for i in range(0, len(variant_list), n_cols):
                            cols = st.columns(n_cols)
                            
                            for col_idx, col in enumerate(cols):
                                if i + col_idx < len(variant_list):
                                    name, variant_data = variant_list[i + col_idx]
                                    
                                    with col:
                                        silhouette = variant_data.get('silhouette', 0)
                                        
                                        # Card header
                                        if name == best_variant:
                                            st.success(f"🏆 {name}")
                                        else:
                                            st.write(f"**{name}**")
                                        
                                        # Metrics
                                        st.metric("Silhouette", f"{silhouette:.3f}")
                                        
                                        if variant_data.get('algorithm') == 'kmeans':
                                            st.metric("K", variant_data.get('k', 0))
                                            st.metric("Inertia", f"{variant_data.get('inertia', 0):.0f}")
                                        else:
                                            st.metric("Clusters", variant_data.get('n_clusters', 0))
                                            st.metric("Noise", variant_data.get('n_noise', 0))
                                        
                                        # Cluster labeling
                                        st.write("**Label Clusters:**")
                                        unique_clusters = sorted(list(set(variant_data.get('labels', []))))
                                        cluster_labels = {}
                                        
                                        for cluster_id in unique_clusters:
                                            if cluster_id != -1:
                                                label = st.text_input(
                                                    f"C{cluster_id}:",
                                                    value="",
                                                    key=f"{name}_c{cluster_id}"
                                                )
                                                cluster_labels[cluster_id] = label if label else f"C{cluster_id}"
                                        
                                        # Approve button
                                        if st.button(f"✅ Approve {name}", key=f"appr_{name}"):
                                            with st.spinner(f"Saving {name}..."):
                                                try:
                                                    # Set selected variant before approval
                                                    workflow_state['selected_variant'] = name
                                                    
                                                    final_state = agentic_orch.approve_selected_clustering(
                                                        workflow_state,
                                                        cluster_labels if cluster_labels else None
                                                    )
                                                    
                                                    if final_state.get('approval_status') == 'approved':
                                                        st.success(f"✓ Saved to final table!")
                                                    else:
                                                        st.error(f"Failed: {final_state.get('error_message')}")
                                                except Exception as e:
                                                    st.error(f"Error: {str(e)}")
                                        
                                        # Visualizations
                                        if 'labels' in variant_data:
                                            st.write("**3D Cluster Visualization:**")
                                            fig_3d = plot_3d_clustering(df, variant_data['labels'], f"{name}")
                                            st.plotly_chart(fig_3d, config={'responsive': True})
                                            
                                            st.write("**Distribution:**")
                                            dist = plot_cluster_distribution(variant_data['labels'], "Count")
                                            st.plotly_chart(dist, config={'responsive': True})
                        
                        # AI Analysis section
                        st.divider()
                        st.subheader("💡 AI Analysis (Reference)")
                        
                        selected_analysis = st.selectbox(
                            "View analysis for:",
                            [name for name, _ in variant_list],
                            key="analysis_select"
                        )
                        
                        for name, variant_data in variant_list:
                            if name == selected_analysis:
                                if 'explanation' in variant_data and variant_data['explanation']:
                                    st.markdown(variant_data['explanation'])
                                else:
                                    st.info("No AI analysis available")
                                break
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("No tables found. Run ingestion first.")

if __name__ == "__main__":
    main()
