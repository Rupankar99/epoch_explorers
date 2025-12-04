#!/bin/bash
# Start Transaction Fraud Detection Dashboard

echo "=========================================="
echo "Transaction Fraud Detection Dashboard"
echo "=========================================="
echo ""
echo "Sample Data Location:"
echo "  CSV:  src/clusterer/data/transactions/transactions.csv"
echo "  JSON: src/clusterer/data/transactions/transactions_additional.json"
echo ""
echo "Config File:"
echo "  src/clusterer/config.yaml"
echo ""
echo "Database:"
echo "  src/clusterer/cluster_data.db"
echo ""
echo "=========================================="
echo ""
echo "Starting Streamlit Dashboard..."
echo "Open browser to: http://localhost:8501"
echo ""

# Change to clusterer directory
cd src/clusterer

# Run Streamlit
streamlit run dashboard_enhanced.py

