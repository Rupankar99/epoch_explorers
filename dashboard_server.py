#!/usr/bin/env python3
"""
RAG Operational Dashboard - Flask Server
Serves the professional dashboard UI and bridges to RAG API
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime
from collections import deque
import threading

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configuration
RAG_API_URL = 'http://localhost:8001'
DASHBOARD_PORT = 8000

# In-memory log storage (max 100 entries)
system_logs = deque(maxlen=100)
logs_lock = threading.Lock()

def add_log(level, message):
    """Add a log entry"""
    with logs_lock:
        timestamp = datetime.now().strftime('%H:%M:%S')
        system_logs.appendleft({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })

# Helper function to call RAG API
def call_rag_api(endpoint, method='POST', data=None):
    """Call the RAG API"""
    try:
        url = f'{RAG_API_URL}{endpoint}'
        if method == 'GET':
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, json=data, timeout=30)
        return response.json(), response.status_code
    except Exception as e:
        return {'error': str(e)}, 500

# Routes
@app.route('/')
def index():
    """Serve dashboard HTML"""
    with open('dashboard.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/health', methods=['GET'])
def health():
    """Check health of RAG API"""
    try:
        response = requests.get(f'{RAG_API_URL}/health', timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'healthy', 'api': 'connected'}), 200
    except:
        pass
    return jsonify({'status': 'unhealthy', 'api': 'disconnected'}), 503

@app.route('/api/ingest', methods=['POST'])
def ingest():
    """Ingest a document"""
    data = request.json
    try:
        result, status = call_rag_api('/ingest', 'POST', data)
        if status == 200 and result.get('success'):
            doc_id = data.get('doc_id', 'unknown')
            chunks = result.get('chunks_saved', 0)
            add_log('info', f'✓ Document {doc_id} ingested ({chunks} chunks)')
        else:
            add_log('error', f'✗ Ingestion failed: {result.get("error", "Unknown error")}')
        return jsonify(result), status
    except Exception as e:
        add_log('error', f'✗ Ingestion error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask():
    """Ask a question"""
    data = request.json
    try:
        result, status = call_rag_api('/ask', 'POST', data)
        if status == 200 and result.get('success'):
            user_id = data.get('user_id', 'unknown')
            user_company = data.get('user_company_id', '?')
            user_dept = data.get('user_dept_id', '?')
            chunks = result.get('context_chunks', 0)
            mode = data.get('response_mode', 'verbose')
            add_log('info', f'✓ Query from user{user_id} (C{user_company}D{user_dept}) - {chunks} chunks [{mode}]')
            if result.get('answer'):
                answer_preview = result.get('answer', '')[:50]
                add_log('info', f'✓ Answer generated: "{answer_preview}..."')
        elif status == 200 and not result.get('success'):
            user_id = data.get('user_id', 'unknown')
            add_log('warning', f'⚠ RBAC: Query blocked for user{user_id}')
        else:
            add_log('error', f'✗ Query failed: {result.get("error", "Unknown error")}')
        return jsonify(result), status
    except Exception as e:
        add_log('error', f'✗ Query error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics from logs"""
    with logs_lock:
        total_logs = len(system_logs)
        info_logs = sum(1 for log in system_logs if log['level'] == 'info')
        warning_logs = sum(1 for log in system_logs if log['level'] == 'warning')
        error_logs = sum(1 for log in system_logs if log['level'] == 'error')
    
    return jsonify({
        'totalLogs': total_logs,
        'infoLogs': info_logs,
        'warningLogs': warning_logs,
        'errorLogs': error_logs,
        'rbacViolations': warning_logs,
        'successRate': f'{(100 * (info_logs / max(total_logs, 1))):.1f}%' if total_logs > 0 else '0%'
    }), 200

@app.route('/api/logs', methods=['GET'])
def logs():
    """Get real system logs"""
    limit = request.args.get('limit', 100, type=int)
    with logs_lock:
        logs_data = list(system_logs)[:limit]
    return jsonify({'logs': logs_data, 'total': len(system_logs)}), 200

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print("  RAG Operational Dashboard Server")
    print(f"{'='*60}")
    print(f"Dashboard: http://localhost:{DASHBOARD_PORT}")
    print(f"RAG API:   {RAG_API_URL}")
    print(f"{'='*60}\n")
    
    app.run(host='127.0.0.1', port=DASHBOARD_PORT, debug=True)
