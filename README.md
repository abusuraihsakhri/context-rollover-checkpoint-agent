# Context Rollover Checkpoint Agent

> **Domain:** Autonomous Agent Systems & Context State Architecture
> **Reference Guidelines & Standards:** `Distributed Systems RFC & State Machine Verification`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Tests](https://img.shields.io/badge/Tests-52_Passed-brightgreen.svg)

</div>

---

## 📖 What It Does

**Context Rollover Checkpoint Agent** is an advanced analytical and computational platform implementing Persistent JSONL event journals & state delta compression for seamless context rollover. It provides:

- **Context Rollover Engine**: Unified checkpoint management, trigger evaluation, and state recovery
- **Zero-PHI Outbound Interceptor**: Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail**: Chained, cryptographically signed logs for every evaluation
- **Multi-Agent Supervisory System**: Coordinated worker agents for comprehensive task evaluation

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`ContextRolloverEngine`**: Unified checkpoint management, trigger evaluation, and state recovery engine
- **`SystemSupervisor`**: Master Distributed Component Coordinator with multi-worker consensus
- **`FrontierDomainEngine`**: Core algorithmic engine for domain threshold boundary validations

### 🔒 Security & Enterprise Architecture

- **`PHIGuard`**: Zero-PHI outbound validation with regex pattern matching
- **`AuditTrail`**: Cryptographic tamper-evident HMAC-SHA256 audit trail with automatic key generation

### 📊 Monitoring & Telemetry

- **`SystemMetricsCollector`**: Prometheus operational metrics exporter
- **`ActiveLearningEngine`**: Bayesian calibration & active learning feedback engine

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/context-rollover-checkpoint-agent.git
cd context-rollover-checkpoint-agent

# Install dependencies (Python 3.9+ required)
pip install pydantic fastapi uvicorn pytest

# Or install as a package
pip install -e .
```

---

## 🚀 Usage

### 1. CLI - Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. CLI - Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. CLI - Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 4. CLI - Verify Audit Trail
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### 6. Run Simulation Benchmark
```bash
python simulator.py 1000
```

---

## 🛡️ Security Features

### Zero-PHI Outbound Guard
Active pattern matching blocks:
- Social Security Numbers (SSN)
- Medical Record Numbers (MRN)
- Phone numbers
- Email addresses
- Date of Birth (DOB) patterns
- Patient name patterns

### HMAC-SHA256 Audit Trail
- **Automatic secure key generation** when no secret is provided
- **Environment variable support** via `AUDIT_SECRET_KEY`
- **Tamper detection** through chained hash verification
- **Integrity verification** for all audit entries

### Path Traversal Protection
- Input validation prevents directory traversal attacks
- Absolute path rejection for file operations
- File existence checks before operations

---

## 🧪 Testing & Verification

### Run All Tests
```bash
pytest tests/ -v -p no:zarr
```

### Test Coverage
- **Trigger Policies**: Token count, time elapsed, error count, context overflow, turn count
- **Checkpoint Compression**: Zlib compression, metadata tracking, roundtrip verification
- **Restore Diff Engine**: Field-level diff calculation, selective restore, nested structures
- **PHI Guard**: Pattern matching, redaction, edge cases
- **Audit Trail**: Key generation, integrity verification, tamper detection
- **Path Traversal Protection**: Input validation, file operations
- **Integration Workflows**: End-to-end checkpoint creation and restoration

### Test Results
```
52 tests passed
```

---

## 📁 Project Structure

```
context-rollover-checkpoint-agent/
├── agents/                      # Multi-agent supervisory system
│   ├── __init__.py
│   ├── api.py                   # FastAPI REST endpoints
│   ├── base.py                  # PHI Guard, Audit Trail, Security
│   ├── learning.py              # Bayesian calibration engine
│   ├── llm_factory.py           # LLM client factory
│   ├── metrics.py               # Prometheus metrics collector
│   ├── models.py                # Pydantic data models
│   ├── streamer.py              # WebSocket telemetry streamer
│   ├── supervisor.py            # Master coordinator
│   └── workers.py               # Specialized domain workers
├── context_rollover/            # Core rollover engine
│   ├── __init__.py
│   ├── agents.py                # State checkpointer coordinator
│   ├── cli.py                   # Alternative CLI interface
│   ├── compression.py           # Checkpoint compression
│   ├── engine.py                # Domain engine
│   ├── models.py                # Data models
│   ├── restore_diff.py          # State diff engine
│   ├── server.py                # FastAPI server factory
│   └── triggers.py              # Rollover trigger policies
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_context_rollover.py
│   ├── test_context_rollover_checkpoint.py
│   ├── test_context_rollover_checkpoint_agent.py
│   ├── test_enrichment.py
│   └── test_security.py         # Security-focused tests
├── cli.py                       # Main CLI entry point
├── context_rollover_app.py      # Alternative app entry point
├── enrichment.py                # Feature enrichment suite
├── pyproject.toml               # Project configuration
├── sample.csv                   # Sample batch input
├── simulator.py                 # High-throughput simulator
└── LICENSE                      # MIT License
```

---

## 🔧 Configuration

### Environment Variables
- `AUDIT_SECRET_KEY`: Optional HMAC secret key for audit trail (auto-generated if not set)

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Entity or target key | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary confidence score | Optional (default: 0.0) |
| `is_critical_flag` | Emergency escalation flag | Optional (default: False) |
| `status_descriptor` | Status code descriptor | Optional (default: "NOMINAL") |

---

## 🐳 Container Deployment

```bash
docker build -t context-rollover-checkpoint-agent .
docker run -p 8000:8000 context-rollover-checkpoint-agent
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
