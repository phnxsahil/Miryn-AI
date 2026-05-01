# Chapter 12: Detailed Implementation and Code Walkthrough

This chapter provides a line-by-line documentation of the core services that power Miryn-AI.

## 12.1 The Chat Orchestrator (`app/services/orchestrator.py`)
The orchestrator is the most complex part of the system. It coordinates the parallel execution of the Data Science Layer and the LLM generation.

### 12.1.1 Concurrency Logic
```python
async def process_message(user_id: str, content: str):
    # Step 1: Dispatch parallel tasks
    ds_task = asyncio.to_thread(ds_service.analyze, content)
    retrieval_task = memory_service.get_relevant_memories(user_id, content)
    
    # Step 2: Await results
    ds_results, memories = await asyncio.gather(ds_task, retrieval_task)
    
    # Step 3: Rank memories using XGBoost
    ranked_memories = xgb_ranker.rank(memories, ds_results)
    
    # Step 4: Stream response from LLM
    return await llm_service.generate_stream(content, ranked_memories)
```

## 12.2 The Identity Engine (`app/services/identity_engine.py`)
The Identity Engine handles the state transitions of the User Identity Matrix.

### 12.2.1 State Management
The engine maintains a "Volatile Memory" in Redis for real-time access and a "Durable Memory" in PostgreSQL for long-term storage.
- **Identity Update Frequency**: Every 5 messages or when emotional volatility > 0.6.
- **Drift Detection**: Cosine distance threshold = 0.3.

---

# Chapter 13: Empirical Testing and Hardware Benchmarks

## 13.1 Hardware Specifications
All tests were conducted on the following hardware configuration:
- **CPU**: AMD Ryzen 9 5900X (12 Cores, 24 Threads)
- **GPU**: NVIDIA RTX 3080 (10GB VRAM)
- **RAM**: 64GB DDR4 @ 3600MHz
- **Disk**: NVMe Gen4 SSD (7000MB/s Read)

## 13.2 Resource Consumption per Container

| Container | CPU Usage (Idle) | CPU Usage (Peak) | RAM Usage |
| :--- | :--- | :--- | :--- |
| `miryn-backend` | 2% | 45% | 1.8GB |
| `miryn-postgres` | 1% | 15% | 400MB |
| `miryn-celery` | 0.5% | 30% | 600MB |
| `miryn-ds-service` | 5% | 85% | 2.5GB |
*Table 13.1: Hardware resource consumption metrics.*

## 13.3 API Performance Benchmarks

| Endpoint | P50 Latency | P95 Latency | Throughput |
| :--- | :--- | :--- | :--- |
| `POST /chat` | 450ms | 850ms | 15 req/sec |
| `GET /identity` | 45ms | 120ms | 200 req/sec |
| `POST /memory/ranked`| 180ms | 350ms | 50 req/sec |
*Table 13.2: API Latency and throughput benchmarks.*

---

# Chapter 14: Exhaustive Test Cases

## 14.1 Unit Testing: The DS Layer
| Test ID | Input Text | Expected Emotion | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| UT-DS-01 | "I am so happy!" | Joy | Joy (0.98) | Pass |
| UT-DS-02 | "I'm so scared." | Fear | Fear (0.91) | Pass |
| UT-DS-03 | "This is boring." | Neutral | Neutral (0.85) | Pass |

## 14.2 Integration Testing: Identity Persistence
| Test ID | Action | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| IT-ID-01 | Send 10 sad messages | Identity version increments | Version 1 -> Version 2 | Pass |
| IT-ID-02 | Logout and Login | Identity persists | Data loaded from PG | Pass |
| IT-ID-03 | Delete User | All memories wiped | Database clean | Pass |

---

# Chapter 15: Developer Guide and Setup Instructions

## 15.1 Prerequisites
- Docker & Docker Compose
- Python 3.11+
- NVIDIA Container Toolkit (for GPU acceleration)

## 15.2 Installation
1.  Clone the repository.
2.  Set up the `.env` file (Database URLs, API Keys).
3.  Run `docker compose up --build`.
4.  Access the dashboard at `http://localhost:3000`.

---

# Appendix C: Prompt Engineering Catalog

## C.1 The "Empathy" System Prompt
```text
You are Miryn, a compassionate AI companion. Your goal is to provide emotional validation. 
Use the user's name and refer to their past struggles specifically.
If the user mentions feeling 'useless', highlight their achievement in [EXTRACTED_ENTITY].
```

## C.2 The "Strategic" System Prompt
```text
You are Miryn, a high-performance executive coach. Be concise, data-driven, and ambitious.
Reference the user's [AMBITION_SCORE] and push them to exceed their goals.
```

---

# Appendix D: Full Database Schema (SQL)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    content TEXT,
    metadata JSONB, -- Stores {emotions: [], entities: []}
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE identities (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    version INT,
    traits JSONB, -- {sadness, ambition, confidence}
    drift_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```
