A Production-Grade Multi-Agent NL→SQL Engine

MultiAgentNL2SQL is a fully modular, multi-layered, multi-agent SQL generation engine that converts natural language questions into safe, validated, executable SQL queries against a relational data warehouse.

It features:

Multi-agent table selection

Multi-agent SQL generation

Multi-agent validation

Multi-agent SQL repair

Schema graph reasoning

Join-path inference

Token reduction (schema compression)

Three-tier orchestrators (Full / Fast / UltraFast)

Async execution with OpenAI and Local LLMs

Safe, read-only SQL execution (DB Execution Layer)

Built for robustness, accuracy, and production readiness.

⚡ Features
🧠 Multi-Agent Architecture

The system uses multiple agents at each stage of the pipeline:

Table Selection Agents

Semantic selector (embeddings)

Heuristic selector

Column-name selector

Schema-graph BFS selector

Fusion selector (weighted ranking)

SQL Generation Agents

Deterministic generator

Canonical generator

Join-heavy generator

Minimal generator

Template-based generator

Local LLM generator (Ollama)

OpenAI generator

Validation Agents

OpenAI semantic validator

Local LLM semantic validator

Structural validator (SQL syntax + intent)

Validator fusion layer

Repair Agents

Grammar fix

Join fix

Column fix

Group-by fix

Dim-date fix

AST canonical rewrite

Semantic fix

OpenAI repair modules

SLM repair modules

Each repair is re-validated.

🔗 Schema Graph + Join Reasoning

The engine builds a schema graph using:

Primary keys

Foreign keys

Table roles (Fact / Dim / Other)

Then performs:

BFS table expansion

Multi-hop join inference

Conflict-free join-path building

Composite-key support

Ensuring correct join chains in all generated SQL.

🧱 Token Reduction Engine

Large schemas are compressed with a 3-part reducer:

Table Summarizer

Keeps only relevant columns

Removes metadata, audit fields, GUIDs

Join Path Summarizer

Summarizes multi-hop FK relationships

LLM Compressor

Optional LLM-based summarization

Enables small, deterministic, safe prompts.

🚀 Three Execution Modes
Mode	Latency	Accuracy	Use Case
UltraFast	0.5–1.2s	Low-Med	Autocomplete, search, previews
Fast	2–6s	High	Dashboards, production queries
Full	8–20s	Very High	Critical analytics, BI workloads
🛡 Safe SQL Execution (DB Executor)

The DB Execution Layer ensures:

Read-only SQL

No UPDATE/DELETE/INSERT/TRUNCATE

No multiple statements

TOP row limits

ORDER BY handling

Timeout enforcement

Clean result normalization

Supports SQL Server (pyodbc) via async thread execution.

🧩 Project Structure
MultiAgentNL2SQL/
│
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routers/
│   │   ├── nl2sql.py           # Full orchestrator
│   │   ├── nl2sql_fast.py      # Fast orchestrator
│   │   └── nl2sql_ultrafast.py # UltraFast orchestrator
│   └── models/
│
├── core/
│   ├── agent.py                # Full multi-agent orchestration
│   ├── agent_fast.py           # Fast orchestration
│   ├── agent_ultrafast.py      # UltraFast orchestration
│   │
│   ├── table_selector/
│   │   ├── selector_agents.py
│   │   └── selectors_ultrafast.py
│   │
│   ├── generation_agents/
│   │   ├── generation_agents.py
│   │   └── generator_ultrafast.py
│   │
│   ├── validator_agents.py
│   ├── repair_agents.py
│   │
│   ├── schema_graph/
│   │   ├── schema_loader.py
│   │   ├── schema_graph.py
│   │   └── path_resolver.py
│   │
│   ├── confidence/
│   │   ├── fusion_confidence.py
│   │   ├── semantic_confidence.py
│   │   ├── similarity_confidence.py
│   │   ├── structural_confidence.py
│   │   └── validator_confidence.py
│   │
│   ├── token_reducer/
│   │   ├── reducer.py
│   │   ├── table_summarizer.py
│   │   ├── join_path_summarizer.py
│   │   └── llm_compressor.py
│   │
│   ├── db/
│   │   ├── db_executor.py
│   │   ├── db_safety.py
│   │   └── db_results.py
│   │
│   └── prompt_builder/
│       ├── prompt_builder.py
│       └── prompt_builder_ultrafast.py
│
└── llm/
    ├── openai_client.py
    ├── ollama_client.py
    └── llm_manager.py

🌐 API Endpoints
1. Full Mode
POST /nl2sql/generate_sql

2. Fast Mode
POST /nl2sql/generate_sql_fast

3. UltraFast Mode
POST /nl2sql/generate_sql_ultrafast


All endpoints accept:

{
  "question": "Total sales by product in 2014"
}

🧪 Example Response (Fast Mode)
{
  "best_sql": "SELECT ...",
  "best_score": 0.91,
  "selected_tables": ["FactInternetSales", "DimProduct", "DimDate"],
  "candidates": [
    [0.91, "SELECT ..."],
    [0.84, "SELECT ..."]
  ],
  "execution_result": {
    "columns": ["Product", "TotalSales"],
    "row_count": 10,
    "rows": [
      {"Product": "Mountain Bike", "TotalSales": 450000}
    ]
  }
}

🛠 Tech Stack

Python 3.10+

FastAPI

SQLAlchemy + pyodbc

pandas

sqlglot

matplotlib / seaborn (optional)

OpenAI GPT models

Local Ollama models

📦 Installation
git clone https://github.com/<username>/MultiAgentNL2SQL
cd MultiAgentNL2SQL
pip install -r requirements.txt

▶️ Running the API
uvicorn api.main:app --reload --port 8000

⚠️ Safety

The DB Execution Layer enforces:

Read-only SQL

No multiple statements

Row limits

Timeout limits

SQL pattern blocking

🧭 Roadmap

 Natural-language summarization of results

 Visualization engine

 Web UI dashboard

 Benchmarks (Spider-style)

 Streaming responses

 Multi-source SQL federation

📜 License

MIT

🤝 Contributing

PRs welcome — especially improvements to:

validation agents

SQL repair heuristics

schema summarization

generation templates

🧠 Acknowledgements

Inspired by research and industry practices from:

Databricks AI

Snowflake Cortex Analytic Functions

Semantic Kernel NL2SQL

Raven NL2SQL

Vanna

SQLGlot