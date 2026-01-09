# SPIN Sales Coach: LLM-as-a-Judge Evaluation Pipeline

_🔗 [You can find the Demo App deployed in Azure here.](https://frontend.icyforest-aa3b4633.southeastasia.azurecontainerapps.io/) It's on free credits so it might be a bit slow load. Performance was not considered on the deployment._

Modern sales teams generate vast amounts of conversational data: calls, demos, discovery sessions, and follow-ups. Yet despite the volume, most of this data isn't actively used. Coaching is still mostly based on opinion, varies a lot, and is hard to scale. It depends on manual checks or surface-level metrics that don’t really show how conversations go.

This project exists to change that.

At its core, this system embodies the “LLM-as-a-Judge” paradigm, using large language models not as creative or generative oracles, but as structured evaluators of human performance, grounded in a defined methodology. Rather than treating conversations as raw text to summarize or focusing purely on outcomes, the system evaluates how effectively a salesperson follows the SPIN (Situation, Problem, Implication, Need-Payoff) framework and produces explainable, measurable assessments that can be compared and improved over time.


This repo is intentionally built as a **reference implementation** of the **LLM-as-a-Judge** pattern:
- evaluation criteria is **explicit, versioned, and testable**
- LLM outputs are treated as **untrusted** until **schema + business-rule validated**
- every assessment is stored for **auditability, analytics, and calibration**
- offline evaluation is built-in (Pearson r, QWK, ±1 accuracy) to support prompt iteration

---

## Table of Contents
- [What it does](#what-it-does)
- [Key features](#key-features)
- [Architecture](#architecture)
- [App file structure](#app-file-structure)
- [Quick Start / Local Setup](#quick-start--local-setup)
- [Configuration](#configuration)
- [Core concepts](#core-concepts)
- [API overview](#api-overview)
- [Research inspiration](#research-inspiration)
- [Known limitations](#known-limitations)
- [Design rationale](#design-rationale)

---

## What it does

Sales teams generate tons of call data, but coaching is still hard to scale and often inconsistent.

This system turns a transcript into **repeatable evaluation artifacts**:

1) **Ingest transcript** (raw + normalized)
2) **Score with LLM** using a SPIN rubric + org-specific prompt template
3) **Validate JSON output** (schema + business constraints)
4) **Persist** transcript + assessment + metadata (prompt/model/version/latency/cost signals)
5) **Evaluate the evaluator** offline against labeled datasets

---

## Key features

- **SPIN-based scoring** (Situation / Problem / Implication / Need-Payoff)
- **Coaching output generation** (wins, gaps, next actions)
- **Strict JSON guardrails** (LLM output validated before storing/serving)
- **Multi-tenant by default** (org-scoped resources)
- **Provider-agnostic LLM calls** (OpenAI / Anthropic / Google via LangChain)
- **Mock mode** (`MOCK_LLM=true`) to run tests without API calls
- **Offline evaluation + calibration** (Pearson r, QWK, ±1 band accuracy)
- **Next.js dashboard** for reviewing transcripts/assessments and basic reporting views

---

## Architecture

This section focuses on the two workflows that matter most in this system: **Assessment** and **Evaluation**. **Assessment** is the core *LLM-as-a-Judge* workflow. It takes a transcript, applies the SPIN rubric, and produces structured scores and coaching output. **Evaluation** is the feedback loop that keeps that judge reliable over time. It benchmarks prompt/model versions against curated “gold standard” datasets so we can measure changes, detect regressions, and iterate safely. This exists because “what good looks like” in SPIN-based sales conversations isn’t fixed: teams evolve, playbooks shift, markets change, and new examples redefine the gold standard. By separating Assessment (producing judgments) from Evaluation (measuring and improving the judge), the system recalibrated as the definition of quality evolves.


### Assessment

The diagram below describes the **Assessment workflow** — the production path where the system turns a raw sales transcript into a **validated, organization-scoped SPIN assessment** with coaching output. This is the “LLM-as-a-Judge” part of the app: the model is not treated as a creative generator, but as a **structured evaluator** operating inside a controlled pipeline with strict contracts, multi-tenant context, and audit-friendly persistence.


<a href="https://github.com/user-attachments/assets/1d4aa417-dc30-4b7d-921e-29a7b2d6af34" target="_blank">
  <img width="500" height="500" alt="Untitled design (1)" src="https://github.com/user-attachments/assets/8b8c25fb-1b0d-45f6-b814-f36600793720" />
</a>

<sub>*Click image to view full size*</sub>


At a high level, the workflow is designed around one principle: **make LLM judgments operationally safe**. That means authenticating first, scoping every action to an organization, treating model output as untrusted until validated, and ensuring every run is traceable (prompt version, model, latency, and errors).

---

#### 1) Authentication + Tenant Context (gate everything early)
Every request begins by validating the caller:
- JWT is verified before any processing
- the authenticated user determines the **organization context**
- failures return immediately (401), avoiding unnecessary compute and preventing cross-tenant leakage

Multi-tenancy is enforced from the first step.

---

#### Phase 1: Persist Transcript (traceability)
Before any scoring happens, the transcript is stored as the system:
- create a transcript record with metadata (rep/buyer IDs if available, call context, etc.)
- obtain a database ID (used as the identifier downstream)
- preserve raw input so the same transcript can be re-scored later when prompts evolve (using evaluations later)

Transcripts are immutable historical records; improvements happen by **re-assessing**, not “editing” the past.

---

#### Phase 2: Score via LLM (the controlled judge)
This phase is where most of the engineering rigor lives — it’s the expensive step and the easiest place for systems to become unreliable if guardrails are missing.

**Prompt assembly**
- fetch the active, versioned prompt template for the organization
- render **system + user prompts** with transcript content and rubric constraints

**Provider-agnostic LLM invocation**
- detect provider from model naming conventions (e.g., `gpt-*`, `claude-*`, `gemini-*`)
- load organization-level provider credentials from the database (with env var fallback for local testing)
- execute the call through a single `call_json` interface so the pipeline stays consistent even as models change

**Strict output handling (LLM output is untrusted)**
- parse response as JSON (no “best effort” parsing)
- validate required keys (scores + coaching)
- enforce business rules:
  - all dimensions present
  - scores must be integers in the 1–5 range
  - coaching structure must include `summary`, `wins`, `gaps`, `next_actions`

**Performance + debuggability**
- measure end-to-end model latency and store it with the assessment
- produce actionable errors when validation fails

The LLM is wrapped in contracts (schema + business rules) so outputs can safely power analytics and coaching at scale.

---

#### Phase 3: Persist Assessment (atomic write + audit trail)
Once validated, the system commits the final evaluation artifact:
- store the per-dimension scores and coaching output
- store model metadata (provider/model/version) and prompt version references
- commit the transaction and return the new `assessment_id`

Every assessment is reproducible. You can answer “what prompt + model produced this result?” months later.

---

### Example response (what the client receives)

```json
{
  "assessment_id": 123,
  "scores": {
    "situation": 4,
    "problem": 3,
    "implication": 4,
    "need_payoff": 3,
    "flow": 4,
    "tone": 4,
    "engagement": 3
  },
  "coaching": {
    "summary": "Strong situation and problem identification...",
    "wins": ["Good rapport building", "Clear problem discovery"],
    "gaps": ["Could explore implications deeper"],
    "next_actions": ["Practice implication questions"]
  }
}
```

### Evaluation

The diagram below shows the **Evaluation workflow**. The part of the system that keeps the **LLM-as-a-Judge** accurate over time. 

<a href="https://github.com/user-attachments/assets/ed289e25-28e9-491e-b23b-40815de7f9f9" target="_blank">
  <img width="500" height="500" alt="Untitled design" src="https://github.com/user-attachments/assets/c6c48a72-cd46-460c-952c-7a03ff90ee12" />
</a>

<sub>*Click image to view full size*</sub>

This exists because sales “gold standards” are not fixed. Teams mature, playbooks change, and new examples redefine what *great* looks like. Evaluation gives the system a way to **measure those shifts** and **update the judge with confidence**, instead of changing prompts blindly.

#### Two ways to run it (same engine)
Evaluation can be triggered through:
- **API**: `POST /evaluations/run` (useful for admin portal workflows)
- **CLI**: `run_evaluation.py` (useful for local runs, experiments, and automation)

Both entry points converge into the same orchestrator, so results stay comparable regardless of how the run is started.

#### Phase 1: Score transcripts (the only expensive step)
This is the heart of the “single-pass” design:
- Load a dataset (CSV) that contains transcripts + ground-truth SPIN scores
- For each transcript:
  - fetch the active prompt template (versioned)
  - build the calibrated prompt (system + user)
  - call the LLM **once**
  - parse + validate the JSON result (schema + score range checks)
  - collect predicted scores per SPIN dimension

The LLM is treated as a *scoring dependency*.

#### Phase 2: Compute metrics (fast, local)
Once predictions exist, the rest is cheap and repeatable:
- **Pearson r** (trend alignment with ground truth)
- **QWK** (ordinal agreement on 1–5 scales)
- **±1 band accuracy** (“close enough” correctness for coaching)
- per-dimension metrics + macro averages

This makes prompt changes measurable, so iteration is driven by evidence, not vibes.

#### Phase 3: Store locally (always)
Every evaluation run is persisted to PostgreSQL:
- prompt version + model metadata
- metrics (per dimension + macro)
- timestamps + run identifiers

Evaluation runs become a permanent record you can compare over time (“Is prompt v12 actually better than v11?”).

#### Phase 4: Push to LangSmith (optional, no extra LLM cost)
If LangSmith is configured, the run can be published for experiment tracking:
- results are pushed using a **mock scorer backed by pre-computed outputs**
- **no re-scoring** → no additional LLM calls
- metrics are attached as experiment metadata + a shareable URL is generated

You get observability and traceability without doubling inference cost — the system separates *scoring* from *reporting*.

---

## App file structure

```text
/
  docker-compose.yml
  docker-compose.demo.yml
  backend/
    app/
      routers/          # assess, auth, transcripts, prompt templates, evaluations, etc.
      models/           # org, user, rep, transcript, assessment, prompt templates, eval datasets
      services/         # scorer, llm_client, evaluation runner, langsmith integrations
      utils/            # json_guardrails, helpers
    alembic/            # migrations
    scripts/            # run_evaluation.py, run_langsmith_eval.py, seed helpers
    docs/               # EVALUATION.md, LANGSMITH.md
  frontend/
    src/app/            # dashboard pages
```

---

## Quick Start / Local Setup

### Prerequisites

* Docker + Docker Compose
* Node.js (optional if you run the frontend outside Docker)

### 1) Create backend env file

Create `backend/.env` (example below).

### 2) Start the stack

From repo root:

```bash
docker compose up --build
```

* Frontend: `http://localhost:3000`
* Backend OpenAPI docs: `http://localhost:8000/docs`
* Health check: `http://localhost:8000/health`

### 3) Run a basic assessment

Once running, you can call the assess endpoint:

```bash
curl -X POST http://localhost:8000/assess \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Rep: Hi — thanks for taking the call.\nBuyer: Sure.\nRep: Can you tell me about your current workflow?\nBuyer: We do it manually...",
    "metadata": {
      "rep_id": "demo-rep",
      "call_context": "discovery"
    }
  }'
```

> Tip: If you set `MOCK_LLM=true`, responses are deterministic and require no provider API keys.

---

## Configuration

### `backend/.env` example

```env
# App
APP_ENV=dev
MOCK_LLM=true

# Database (Docker compose expects Postgres; Alembic reads DATABASE_URL)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/llmpaa

# Auth
JWT_SECRET=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional: encryption for stored org LLM credentials
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=

# Optional: provider keys (only needed when MOCK_LLM=false)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Optional: LangSmith (for eval + tracing)
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=spin-scoring

# Optional: CORS
FRONTEND_URL=http://localhost:3000
```

---

## Core Concepts

I’ve defined a shared vocabulary for how sales conversations are ingested, assessed, evaluated, and coached. This feels non-technical, but it is critical infrastructure for an AI system.

This section defines the core terms used throughout the system.

### Transcript

A **Transcript** is the canonical representation of a sales conversation.

It is the primary input to the system and represents what actually happened during a call, demo, or discovery session.

A transcript includes:

- Speaker turns (e.g. sales rep, prospect)
- Timestamps or ordering
- Optional metadata (organization, representative, call context)

**Key principle:**  
Transcripts are immutable historical records.  
We never “fix” a transcript — we only re-evaluate it as prompts, rubrics, or models evolve.

---

### Assessment

An **Assessment** is a single, structured evaluation of a transcript.

It represents the system’s judgment of how well a conversation was conducted, based on a defined framework (e.g., SPIN).

An assessment:

- Is generated by an LLM (prompt-driven)
- Produces structured, machine-readable output
- Is tied to a specific prompt template and model version

Multiple assessments can exist for the same transcript over time.

---

### SPIN Dimensions

The system evaluates conversations using the **SPIN selling framework**, broken into four independent dimensions.

Each dimension is scored and reasoned about separately.

| SPIN Dimension | Description |
|---------------|-------------|
| **Situation** | How effectively the representative establishes context about the prospect’s current state, environment, and constraints. |
| **Problem** | How well the representative uncovers explicit pain points, challenges, or inefficiencies. |
| **Implication** | How clearly the representative explores the consequences of those problems if left unresolved. |
| **Need–Payoff** | How effectively the representative helps the prospect articulate the value, outcomes, or benefits of solving the problem. |


---

### Coaching Output

**Coaching Output** is the human-readable layer built on top of an assessment.

It translates structured scores and rationales into actionable guidance for a sales representative.

Typical coaching output includes:

- **Summary** – a concise, high-level read of the conversation
- **Wins** – what was done well and should be repeated
- **Gaps** – missed opportunities or weak signals
- **Next Actions** – concrete suggestions for improvement

This is where the system creates real business value.

---

### Prompt Template

A **Prompt Template** defines how the LLM is instructed to perform an assessment.

It includes:

- Role instructions (e.g. “senior sales coach”)
- Scoring rubric definitions
- Output schema constraints
- Formatting and validation rules

Prompt templates are versioned artifacts.

Changing a prompt does not overwrite prior assessments; it creates new ones.

---

### Evaluation Dataset

An **Evaluation Dataset** is a curated collection of transcripts used to measure system quality.

These datasets are used to:

- Compare prompt versions
- Compare models (prompt-driven vs fine-tuned)
- Track regression or improvement over time

Datasets may include:

- “Gold standard” conversations
- Edge cases
- Known failure modes

**Key principle:**  
Evaluation datasets exist to measure system behavior, not to train intuition.

---

### Evaluation Run

An **Evaluation Run** is a repeatable execution of the system over an evaluation dataset.

An evaluation run captures:

- Prompt version
- Model identity
- Scores and outputs
- Aggregate metrics (e.g. correlation, variance, agreement)

Evaluation runs allow the system to answer:

> “Is this version better than the last?”

---

### Organization

An **Organization** represents a tenant in the system.

Organizations define:

- Their own scoring preferences
- Prompt customizations
- Evaluation datasets
- Access boundaries

Organizations are isolated by design.

---

### Representative

A **Representative** is the individual being assessed and coached.

Assessments are always contextual:

- A score is not “good” or “bad” in isolation
- It is interpreted relative to a representative’s history, role, and goals

---

## API overview

The backend is a FastAPI app with routers for:

* `/assess` (score + generate coaching)
* `/auth/*` (register/login/me/refresh)
* `/transcripts/*`
* `/prompt-templates/*`
* `/evaluations/*` (offline evaluation dataset/run tracking)
* `/overview/*` (dashboard aggregates)

Explore all endpoints at:

* `http://localhost:8000/docs`

---

## Research inspiration

This project is heavily informed by the emerging “LLM-as-a-Judge” literature and evaluator design patterns:

* **Zheng et al. (2023)** — *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* ([arXiv][1])
* **Liu et al. (2023)** — *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment* ([arXiv][2])
* **Kim et al. (2024)** — *Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models* ([arXiv][3])
* **Chen et al. (2024)** — *Humans or LLMs as the Judge? A Study on Judgement Bias* ([ACL Anthology][4])
* **Huang et al. (2025)** — *An Empirical Study of LLM-as-a-Judge for LLM Evaluation* ([ACL Anthology][5])

---

## Known limitations

* **Transcript ingestion is manual** (file upload / form). No native call platform integrations yet.
* **Audio processing is out of scope** (no diarization/ASR in this repo).
* **Authentication story is evolving**: JWT flows exist; an API-key helper exists but isn’t consistently wired across routes yet.
* **Prompt management UX is MVP-level** (sufficient for iteration, not a finished product).
* **Analytics are foundational** (core aggregates exist; deeper coaching insights and longitudinal reporting can be expanded).
* **Guardrails focus on structure** (schema/range validation). Content safety/policy layers can be added depending on deployment context.

---

# Design rationale

Explainations **why** the system looks the way it does, what tradeoffs were made, and what future upgrades are straightforward.

## A. Why SPIN + structured judging?

Honestly it could be any selling framework but I choose SPIN breaks “good discovery” into separable behaviors. That makes it suitable for:

* **dimension-wise scoring** (instead of a vague overall grade)
* **actionable coaching** (“you skipped implication exploration”)
* **measurable iteration** (did our prompt improve implication correlation?)

## B. Why prompt-driven evaluation (not fine-tune)?

Fine-tuning can be powerful. I wanted to build an app for real sales orgs that would not rely on AI engineers or Data scientists to operate. Labeled datasets are expensive and slow and scoring policies change as teams mature or learns from effective sales conversations. Prompt iteration is faster, cheaper, and easier to audit.

## C. Why JSON guardrails?

If you want reliable analytics, you need reliable outputs.
So the LLM is treated like:

* a probabilistic function that can fail
* an upstream dependency that must be validated

Guardrails convert “LLM text” into **safe evaluation artifacts**. It's also easier to build UI from a reliable JSON response.

## D. Why store *everything* (prompt/model/latency metadata)?

The idea to be able to tweak the evaluation as soon as the market response for the sales tactics change. Evaluation systems regress silently.

Storing metadata enables:
* reproducibility (“what prompt produced this score?”)
* cost/perf tuning (token usage, latency distributions)
* drift analysis (changes in score distributions over time)
* auditability for coaching decisions

## E. Why offline evaluation metrics (Pearson r, QWK, ±1)?

When we evaluate the prompts that does the assessments of SPIN framework agains a **gold set**, there are three different questions that should be asked:

1. Do we rank conversations the same way? (trend alignment)
2. Do we agree on the actual 1-5 ratings as ordinal judgements?
3. Even when we disagree, are we close enough that coaching wouldn't materially change?

### Pearson r (correlation): “Do we move in the same direction?”

**What it measures:** Whether model scores rise/fall with ground truth across examples.

- If the gold set says Transcript A is better than B on “Implication,” Pearson r checks whether the prompt tends to reflect the same ordering.
- This is useful when you care about **relative ranking**: who’s improving, which calls are strongest/weakest, trend lines over time.

**Why it matters for prompts:**  
Prompt changes often shift the *scale* (e.g., becoming stricter/lenient) but still preserve ordering. Pearson r will still look good in that case—correctly signaling “the prompt tracks the same signal.”

**Where it can mislead:**  
High correlation doesn’t guarantee the ratings match (you can be consistently +1 or -1 everywhere and still correlate well). That’s why you need QWK and ±1.

---

### QWK (Quadratic Weighted Kappa): “Do we agree on 1–5 ratings, with ordinal penalties?”

**What it measures:** Agreement on ordinal categories (1–5), penalizing larger disagreements more than small ones.

- Predicting 4 when truth is 5 is a *small* mistake.
- Predicting 1 when truth is 5 is a *big* mistake.
- QWK bakes that into the score.

**Why it’s a great fit here:**  
SPIN scores are **ordinal**, not truly interval. The difference between 2→3 isn’t guaranteed to mean the same as 4→5. QWK respects that by treating ratings as ordered categories, not continuous measurements.

**Why it matters for prompts:**  
If Prompt v12 becomes “harsh” on Problem discovery (lots of 2s instead of 4s), QWK will drop because it detects systematic disagreement, even if Pearson r stays decent.

---

### ±1 band accuracy: “Is it close enough for coaching to stay consistent?”

**What it measures:** The percentage of predictions that fall within 1 point of the ground truth (e.g., truth=4, prediction ∈ {3,4,5}).

**Why it matters in coaching:**  
In sales coaching, exactness is often less important than being in the right neighborhood. A 4 vs 5 typically leads to similar coaching advice (“good, keep going”), while a 2 vs 5 changes the narrative completely.

So ±1 accuracy answers a very practical question:

> “If this prompt grades a rep slightly differently, would the *coaching outcome* still be roughly the same?”

**Why it matters for prompts:**  
It’s a reality-check metric. You can have:
- okay correlation,
- okay QWK,
- but still too many “wild misses” that break trust.  
  ±1 accuracy surfaces that.

---

### Why the trio is better than “one accuracy number”

Plain accuracy (“exact match”) is too brittle for 1–5 rubric scoring:

- It treats 4 vs 5 the same as 1 vs 5 (both “wrong”).
- It punishes reasonable rubric interpretation differences.
- It doesn’t tell you whether the prompt is still *useful for coaching*.

Using all three gives you a more honest picture:

- **Pearson r** → *Does the prompt track the same signal / ranking?*
- **QWK** → *Does it agree as an ordinal judge (and avoid big disagreements)?*
- **±1** → *Is it good enough for real coaching without overfitting to exact labels?*

---

### How to interpret them together (quick heuristics)

- **High r, low QWK** → prompt ranks correctly but is systematically stricter/looser (calibration issue).
- **Low r, decent ±1** → prompt is “close” but noisy; rankings/trends may be unreliable.
- **Decent QWK, low ±1** → rare but usually means disagreements cluster at edges (e.g., lots of 1 vs 3/4 misses).
- **All three improve** after a prompt change → strong evidence the prompt got better (and safer to roll out).


---



## F. Why FastAPI + Next.js?

* FastAPI: typed contracts, async LLM calls, clean service decomposition
* Next.js: fast iteration on internal tools, SSR dashboards, strong DX


## G. Why LangChain?

I wanted to find a proven framework to integrate with LLMs. It had to be agnostic and a mature framework. LangChain fit the bill.
