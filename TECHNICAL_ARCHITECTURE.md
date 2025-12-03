# Technical Architecture

## Overview
The `epoch_explorers` project implements a Retrieval-Augmented Generation (RAG) system to enhance information retrieval and response generation. The architecture is modular, leveraging APIs, vector databases, and machine learning models to provide scalable and efficient solutions.

---

## Components

### 1. **Document Ingestion**
- **Purpose**: Preprocess and store documents for retrieval.
- **Key Tools**: `ingestion_tools.py`
- **Workflow**:
  - Chunk documents into smaller pieces.
  - Generate metadata and embeddings.
  - Store embeddings in ChromaDB.

### 2. **Vector Store**
- **Purpose**: Store and retrieve document embeddings.
- **Technology**: ChromaDB
- **Path**: `src/database/data/chroma_db`
- **Workflow**:
  - Store embeddings during ingestion.
  - Query embeddings for similarity-based retrieval.

### 3. **Retrieval**
- **Purpose**: Retrieve relevant document chunks based on user queries.
- **Key Tools**: `retrieval_tools.py`
- **Workflow**:
  - Convert user queries into embeddings.
  - Retrieve relevant chunks using similarity scores.

### 4. **Augmentation**
- **Purpose**: Combine retrieved chunks with user queries to provide context.
- **Key Tools**: `retrieval_tools.py`
- **Workflow**:
  - Append retrieved chunks to the user query.
  - Pass the augmented input to the language model.

### 5. **Generation**
- **Purpose**: Generate responses using the augmented input.
- **Key Tools**: Language models configured in `llm_config.json`
- **Workflow**:
  - Send augmented input to the language model.
  - Generate responses based on the context.

### 6. **API Interaction**
- **Purpose**: Expose the RAG workflow via APIs.
- **Key Tools**: `run_api.py`
- **APIs**:
  - LangGraph API: Handles retrieval and generation.
  - DeepAgents API: Orchestrates additional workflows.

### 7. **Logging and Analytics**
- **Purpose**: Track queries, responses, and system performance.
- **Key Tools**: `rag.db`
- **Workflow**:
  - Store query logs and response metadata.
  - Generate insights using analytics tools.

### 8. **Guardrails**
- **Purpose**: Ensure response quality and optimize workflows.
- **Key Tools**: `custom_guardrails.py`
- **Workflow**:
  - Validate responses against predefined rules.
  - Optimize retrieval and generation processes.

---

## Data Flow
1. **Input**: User queries are received via APIs.
2. **Processing**:
   - Queries are converted into embeddings.
   - Relevant document chunks are retrieved.
   - Retrieved chunks are combined with the query.
   - The augmented input is sent to the language model.
3. **Output**: Responses are generated and returned to the user.

---

## Key Directories
- **`src/rag/agents`**: Contains LangGraph and DeepAgents APIs.
- **`src/rag/tools`**: Includes tools for ingestion, retrieval, and classification.
- **`src/database/models`**: Defines database models.
- **`src/database/migrations`**: Handles database schema creation.

---

## Technologies Used
- **Programming Language**: Python
- **Database**: SQLite (for metadata), ChromaDB (for embeddings)
- **Frameworks**: FastAPI, Uvicorn
- **Environment Management**: dotenv

---

## Deployment
- **APIs**:
  - LangGraph: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Commands**:
  - Start LangGraph: `python run_api.py langgraph`

---

## Future Enhancements
- Implement advanced guardrails for better response validation.
- Optimize embedding storage and retrieval performance.
- Add support for additional language models.

---

## Contributors
- **Owner**: Rupankar99
- **Branch**: sourav

---

For more details, refer to the project documentation or contact the development team.