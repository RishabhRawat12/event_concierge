# Event Concierge: Venue Orchestration System

[![Backend CI](https://github.com/RishabhRawat12/event_concierge/actions/workflows/backend.yml/badge.svg)](https://github.com/RishabhRawat12/event_concierge/actions/workflows/backend.yml)

High-concurrency venue coordination service utilizing Vertex AI for constrained itinerary generation and personnel protocol synchronization.

## System Architecture

The system implements a strictly layered, decoupled architecture designed for horizontal scalability:

### 1. Unified Entry Point (`main.py`)
Centrally manages the application lifecycle, router registration, and exception handling orchestration.

### 2. Business Logic Layer (`/server/services`)
- **Agent Service**: Orchestrates LLM reasoning using Gemini 1.5 Flash with tool-integrated grounding.
- **Itinerary Service**: Coordinates between the spatial engine and AI suggester to produce optimized attendee schedules.
- **Spatial Engine**: Employs Dijkstra's algorithm for sub-millisecond path resolution between venue locations.

### 3. Infrastructure Layer (`/server/infrastructure`)
- **Persistence**: Real-time state management via Cloud Firestore.
- **Caching & Coordination**: High-performance transient storage and Pub/Sub distribution via Redis.
- **Analytics**: Asynchronous analytical ingestion into Google BigQuery.

### 4. Security Framework
- **Identity**: JWT verification via Firebase Admin SDK.
- **Middleware**: Decoupled modules enforcing standard HTTP security headers (nosniff, HSTS, CSP).
- **Validation**: Strict Pydantic V2 schema enforcement for all ingress/egress points.

## Performance Benchmarks

Measured on standard local infrastructure (8-core CPU, 16GB RAM) using the `scripts/benchmark.py` utility:

| Metric | Average Latency | Peak Throughput |
| :--- | :--- | :--- |
| Dijkstra Path Resolution | 0.82ms | 1,200+ req/sec |
| Redis Cache Probe | 2.05ms | 800+ req/sec |
| Itinerary Synthesis (Cold) | 1,750ms | N/A (LLM bound) |
| WebSocket State Push | 42.0ms | 500+ clients/sec |

## Local Execution

### Containerized Startup
```bash
docker-compose up --build
```

### Manual Service Deployment
1. **Server**: `cd server && pip install -r requirements.txt && uvicorn main:app --reload`
2. **Client**: `cd client && npm install && npm run dev`

## Quality Assurance

The system utilizes high-fidelity integration testing to verify distributed state consistency across the Redis and Firestore layers.

- Run full test suite: `pytest` (from `/server`)
- Run performance benchmarks: `python scripts/benchmark.py`
