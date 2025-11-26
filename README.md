# NL2SQL Multi-Agent System



                ┌───────────────────────────────┐
                │         User Question          │
                └───────────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │ Preprocessing    │
                        │ - normalize text │
                        │ - extract years  │
                        │ - detect entity  │
                        └──────────────────┘
                                   │
                                   ▼
            ╔══════════════════════════════════════════════╗
            ║                TABLE AGENTS                  ║
            ║──────────────────────────────────────────────║
            ║ 1. Semantic Selector Agent                   ║
            ║ 2. Heuristic Selector Agent                  ║
            ║ 3. Schema Graph Selector Agent               ║
            ║ 4. Vector Similarity Agent                   ║
            ║ 5. Rule-Based Dimension Expander             ║
            ╚══════════════════════════════════════════════╝
                                   │
                                   ▼
                        Fusion & Scoring
                    (weighted table selection)
                                   │
                                   ▼
                ┌───────────────────────────────┐
                │      Prompt Builder Agent     │
                │  - token reducer              │
                │  - rules: time, dims, joins   │
                │  - schema slicing             │
                │  - example selection          │
                └───────────────────────────────┘
                                   │
                                   ▼
       ╔══════════════════════════════════════════════════════╗
       ║            PARALLEL SQL GENERATION AGENTS           ║
       ║──────────────────────────────────────────────────────║
       ║  Agent G1: deterministic template (temp=0.0)         ║
       ║  Agent G2: soft template (temp=0.2)                  ║
       ║  Agent G3: join-heavy template                       ║
       ║  Agent G4: minimal style                             ║
       ║  Agent G5: canonical style                           ║
       ╚══════════════════════════════════════════════════════╝
                                   │
                                   ▼
                       Candidate SQL Set (5)
                                   │
                                   ▼
                ┌───────────────────────────────┐
                │     SQL Validation Layer      │
                │  - AST validation             │
                │  - schema validation          │
                │  - join path validator        │
                │  - grouping validator         │
                │  - date/dim validator         │
                └───────────────────────────────┘
                                   │
                          Pass? ───┴─── No
                                   ▼
     ╔═════════════════════════════════════════════════════════════╗
     ║                 PARALLEL REPAIR AGENTS                      ║
     ║─────────────────────────────────────────────────────────────║
     ║  R1: Grammar Fix Agent       (local LLaMA/Qwen)             ║
     ║  R2: Join Repair Agent       (add FK joins via schema graph)║
     ║  R3: Column Repair Agent     (fix col names)                ║
     ║  R4: Group Summarization Fix (GROUP BY repair)              ║
     ║  R5: Dim Table Agent         (add missing dims)             ║
     ║  R6: AST Rewrite Agent       (canonical rewrite)            ║
     ║  R7: Intent Alignment Agent  (semantic fix)                 ║
     ╚═════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
             Re-validate repaired candidates in parallel
                                   │
                                   ▼
                       Best Valid SQL Candidate
                                   │
                                   ▼
       ╔══════════════════════════════════════════════════════╗
       ║              CONFIDENCE AGGREGATION AGENTS          ║
       ║──────────────────────────────────────────────────────║
       ║  - structural score                                  ║
       ║  - schema accuracy score                             ║
       ║  - embedding similarity (ESS)                        ║
       ║  - agent agreement score (G1–G5 consistency)         ║
       ║  - repair depth score                                ║
       ║  - canonical SQL similarity                          ║
       ╚══════════════════════════════════════════════════════╝
                                   │
                                   ▼
                ┌───────────────────────────────┐
                │         Final SQL              │
                │     + Confidence Score         │
                └───────────────────────────────┘


🧩 2. Agent Categories (6 Total)
🔵 (1) Table Selection Agents

Each agent brings a different signal:

semantic embedding agent

heuristic keyword agent

schema-graph adjacency agent

vector-store similarity agent

rule-based dims & dates agent

fact-table grounding agent

→ Fusion agent merges these signals.

🔵 (2) SQL Generation Agents

Multiple variants of GPT-4.1-mini:

deterministic

merged schema-heavy

compressed context

join-optimized

minimal structure

→ Running in parallel improves diversity & correctness.

🔵 (3) SQL Validation Agents

AST validator

schema validator

join-path validator

grouping validator

date-dimension validator

column presence validator

→ All deterministic, non-LLM.

🔵 (4) Repair Agents (Local LLaMA/Qwen, fast)

grammar fixer

join fixer

grouping fixer

dim table injector

canonicalizer

missing filters fixer

alias resolver

schema mismatch resolver

AST rewriter

→ All run concurrently.

🔵 (5) Semantic Validator Agent

Small LLM used to answer:

“Does SQL X answer question Y?”

It catches mistakes deterministic validators can’t.

🔵 (6) Confidence Agents

Signals fused to produce final confidence:

structural

semantic

model agreement

embedding similarity

repair depth

validation strength



🧬 3. Multi-LLM Strategy
Step	LLM Used	Why
Generation	GPT-4.1-mini parallel	Best SQL generation
Repair	Local Ollama models	Fast, cheap, iterative
Semantic Validation	Small local or GPT-4.1-mini	Intent correctness
Confidence	Small local	Lightweight reasoning

This hybrid model is faster, cheaper, and more accurate than using GPT-4.1 alone.

🧱 4. Execution Model

Everything runs under:

asyncio for concurrency

race-to-first-success model

timeout management

retry windows

structured logging

🧠 5. Why This Is the Best Design

Because it:

removes reliance on one model

handles failure gracefully

repairs itself

validates structurally and semantically

uses schema and AST for guarantees

maximizes accuracy

minimizes cost

is enterprise safe

This is the same architecture used in highly reliable internal systems.



🧩 Your Final Architecture = Multi-Agent, Multi-LLM, Multi-Validator

The Ultimate NL→SQL Agent becomes a coordinated team of specialized agents, each performing one function extremely well.

Agents:

5× SQL generation agents

5× SQL repair agents

3× table selection agents

1× semantic validator agent

1× confidence agent

multiple AST + schema agents

Orchestrator:

manages concurrency

collects outputs

selects best candidate

retries repair loops

merges agent votes

ensures safety





User Question
     ↓
   Preproc
     ↓
───────────────
TABLE SELECTION
───────────────
  Semantic Selector      → Embeddings
  Heuristic Selector     → Keyword & schema signals
  Graph Selector         → Schema graph reasoning
  Fusion Engine          → Weighted ensemble
     ↓
Selected tables
     ↓
───────────────
  PROMPT BUILDER
───────────────
  Rules (dims, time, joins)
  Token reducer
  Example selector
  Schema slicing
     ↓
Master Prompt
     ↓
─────────────────────────────────────────────
 PARALLEL SQL GENERATION (GPT-4.1-mini x 3)
─────────────────────────────────────────────
   candidate_sql_1 ← temp=0.0, deterministic
   candidate_sql_2 ← temp=0.3, creative
   candidate_sql_3 ← prompt variant + seed
     ↓
Combine candidates
     ↓
───────────────
    VALIDATOR
───────────────
  AST validation
  Schema validation
  Join-path validator
  Group-by validator
  Date/Dim validator
     ↓
If all good → return best
Else →
─────────────────────────────────────────────
  PARALLEL SQL REPAIR (OLLAMA local + AST)
─────────────────────────────────────────────
  repair_sql_1 ← grammar fix
  repair_sql_2 ← missing join repair
  repair_sql_3 ← dim table expansion
  repair_sql_4 ← canonical rewrite
  repair_sql_5 ← AST rewrite
     ↓
Re-validate repairs
     ↓
───────────────
CONFIDENCE ENGINE
───────────────
  Structural score
  Schema score
  Self-consistency score
  Embedding similarity
     ↓
Final SQL


📌 How They Compare — Detailed Difference Table
Capability	Old Structure	New Multi-Agent Structure
Single SQL Generator	✔ yes	✔ included
Multiple SQL Generators (G1–G5)	❌ no	✔ yes (agents/generation_agents.py)
Single Repair Engine	✔ yes	✔ included
Multiple Repair Agents (R1–R7)	❌ no	✔ yes (agents/repair_agents.py)
Single Validator	✔ yes	✔ included
Semantic Validator Agent	❌ no	✔ yes
Table Selection Modules	✔ yes	✔ included
Table Selection Agents (semantic, graph, heuristic)	❌ no	✔ yes
Multi-LLM orchestration	❌ no	✔ yes
Async parallel execution	❌ no	✔ yes
Multi-agent orchestrator	❌ no	✔ part of core/agent.py
Repair concurrency	❌ no	✔ yes
Generation concurrency	❌ no	✔ yes


A) Integrate multi-LLM client layer
B) Build the agent interface (abstract base classes)
C) Create the first SQL generation agents
D) Create the first repair agents
E) Build orchestrator skeleton with asyncio parallelism


✔ The new (Option C arch) ZIP

includes everything the old one had
+ a new agents layer
+ support for parallelism
+ multi-LLM layout
+ multi-agent orchestration

This new folder is where we define:

multiple SQL generators (G1, G2, G3, G4, G5)

multiple repair agents (R1–R7)

multiple table selector agents

multiple validator agents

parallel orchestrations

✔ It reflects the multi-agent, multi-LLM, multi-repair, parallel execution design



ultimate_nl2sql_optionC_arch/
│
├── api/
│   ├── main.py
│   ├── routers/
│   └── models/
│
├── agents/
│   ├── generation_agents.py      # parallel GPT-4.1-mini variants
│   ├── repair_agents.py          # local SLM repair workers
│   ├── selector_agents.py        # multi-agent table selectors
│   └── validator_agents.py       # semantic validation agents
│
├── core/
│   ├── agent.py                  # orchestrator scaffold
│   ├── config.py
│   │
│   ├── utils/
│   ├── schema_graph/
│   ├── ast_guardrails/
│   ├── table_selection/
│   ├── sql_generation/
│   ├── sql_validation/
│   ├── sql_repair/
│   └── confidence/
│
├── llm/                          # LLM wrapper layer
│
├── frontend/
│   └── app.py                    # Streamlit UI scaffold
│
└── README.md


multiple SQL generators (G1, G2, G3, G4, G5)

multiple repair agents (R1–R7)

multiple table selector agents

multiple validator agents

parallel orchestrations



1️⃣ Multi-LLM Client Layer (OpenAI + Ollama)

llm/
 ├── openai_client.py
 ├── ollama_client.py
 └── llm_manager.py   <-- orchestrates parallel calls & retry logic





2️⃣ Agent Abstract Classes (Interfaces)
3️⃣ Selector Agents
4️⃣ SQL Generation Agents
5️⃣ Validation Agents
6️⃣ Repair Agents
7️⃣ Multi-Agent Orchestrator
8️⃣ UI Integration (Streamlit) (optional, at the end)

