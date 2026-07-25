# Regulation Compliance Agent

A proof-of-concept application that extracts marketing compliance rules from CySEC regulatory circulars and evaluates marketing text against those rules using an LLM.

## Architecture

```text
                 +----------------+
                 |  constants.py  |
                 +----------------+
                         │
                         ▼
                  +-------------+
                  |  main.py    |
                  +-------------+
                  /             \
                 /               \
                ▼                 ▼
      +----------------+   +------------------+
      | RuleExtractor  |   | ComplianceEvaluator |
      +----------------+   +------------------+
               │                    │
               ▼                    ▼
         +-------------+      +-------------+
         |   llm.py    |      |   llm.py    |
         +-------------+      +-------------+
               │                    │
               └──────────┬─────────┘
                          ▼
                    OpenAI API
```

## Processing Flow

```text
PDF URLs
    │
    ▼
Download PDFs (async)
    │
    ▼
Extract PDF text
    │
    ▼
LLM extracts compliance rules
    │
    ▼
rules.json
    │
    ▼
User marketing text
    │
    ▼
LLM evaluates against all rules
    │
    ▼
Compliance report
```

## Modules

| Module | Responsibility |
|---------|----------------|
| `main.py` | Loads configuration, initializes the pipeline and runs extraction/evaluation. |
| `constants.py` | Application configuration, prompts and PDF URLs. |
| `models.py` | Pydantic models for configuration, rules and evaluation results. |
| `llm.py` | LangChain/OpenAI client and the extraction/evaluation chains. |
| `extraction.py` | Downloads PDFs concurrently, extracts text and generates `rules.json`. |
| `evaluation.py` | Loads extracted rules, evaluates user text and renders the final report. |

## Installation

```bash
pip install -e .
```

Create a `.env` file:

```text
OPENAI_API_KEY=...
LLM_MODEL=gpt-4.1-mini
```

## Usage

### Extract compliance rules

Extract rules from the regulation PDFs and save them to `data/rules.json`.

```bash
python -m compliance_agent.main --extract
```

This step only needs to be run once, or whenever the source regulations change.

### Evaluate marketing text

Evaluate a piece of marketing text against the extracted rules.

```bash
python -m compliance_agent.main \
  --evaluate "Open a retail CFD account today and receive a 50% deposit bonus."
```

### Extract and evaluate

```bash
python -m compliance_agent.main \
  --extract \
  --evaluate "Open a retail CFD account today and receive a 50% deposit bonus."
```

### Run the golden dataset

Evaluate the implementation against the provided golden dataset.

```bash
python evaluate.py
```

## Architectural Design Decisions

- The solution separates **rule extraction** (one-time) from **compliance evaluation** (repeated). Regulatory PDFs are processed only once to extract structured rules, which are persisted in `rules.json`. Since regulations change infrequently and evaluation requires only the extracted rules, the original PDF content is not retained or indexed.
- PDFs are processed entirely in memory, avoiding unnecessary temporary storage.
- Both extraction and evaluation use structured LLM output (Pydantic models) to ensure deterministic, machine-readable results.
- A simple sequential workflow was chosen because the processing steps are fixed and deterministic, making agent orchestration unnecessary.
- RAG, vector databases, and LangGraph were intentionally omitted because the extracted rule set fits comfortably within the model context and can be evaluated in a single pass.

## Key Prompt Design Decisions

The extraction prompt maximizes recall by extracting every distinct actionable requirement, while the evaluation prompt maintains precision by reporting only violations explicitly supported by both the regulation and the supplied marketing text.

### Rule extraction
- Extract only actionable marketing compliance requirements.
- Ignore background information, regulatory history and administrative guidance.
- Preserve traceability by recording the source document, page number and supporting quote for every extracted rule.

### Compliance evaluation
- Report only violations supported by evidence from the supplied text.
- Return concise, actionable explanations without legal reasoning.
- Deduplicate similar findings into a single user-facing issue.
- Reference the applicable rule ID(s) as supporting evidence.

## Observations

One key observation was that regulatory documents are written for human readers rather than machine processing. Mandatory requirements are mixed with explanatory guidance, illustrative examples, and recommendations, without a consistent structure or format. Achieving reliable rule extraction and compliance evaluation therefore required carefully designed prompts to identify actionable requirements, distinguish them from non-binding content, and report only findings explicitly supported by both the regulations and the supplied marketing text. This also motivated the architecture: since only the extracted compliance rules are required during evaluation, the original PDFs do not need to be retained or embedded. Instead, the documents are processed once to produce a structured rule set that can be reused for subsequent evaluations.

## Future Improvements

With more time, the solution could be extended by:

- Storing extracted compliance rules in a dedicated rule store (e.g., a database with metadata and embeddings) instead of `rules.json`, enabling scalable retrieval and management of large regulatory rule sets.
- Using RAG to retrieve only the most relevant compliance rules from the rule store instead of loading the full rule set.
- Building a LangGraph workflow with separate retrieval, evaluation, and validation steps.
- Exposing the compliance engine through a REST API for automation and a web UI for user-friendly compliance checks.
- Supporting incremental rule updates when regulations change instead of rebuilding the entire rule set.
- Expanding the golden dataset with additional real-world marketing examples and automated regression testing.
- Supporting multiple jurisdictions (e.g., FCA, ESMA, CySEC) through pluggable regulation packs.