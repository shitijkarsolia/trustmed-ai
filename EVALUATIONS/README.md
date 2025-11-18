# EVALUATIONS

This directory contains evaluation scripts and results for the TrustMed AI system.

## Contents

### `evaluations.py`
Python script for evaluating the RAG system using TruLens metrics.

**Key metrics evaluated:**
- **Answer Relevance** - How well the generated answer addresses the user's question
- **Context Relevance** - How relevant the retrieved context is to the query
- **Groundedness** - How well the answer is supported by the retrieved documents

### Evaluation Results

#### `consolidated_trulens.png`
Consolidated visualization of TruLens evaluation metrics across multiple queries.

#### `indi_query.png`
Individual query evaluation results showing detailed performance metrics.

## TruLens Integration

The project uses [TruLens](https://www.trulens.org) for comprehensive RAG evaluation:
- Tracks answer quality and relevance
- Measures context retrieval effectiveness
- Validates response groundedness in source documents
- Provides visual dashboards for monitoring system performance

## Running Evaluations

```bash
cd EVALUATIONS
pip install trulens-eval
python evaluations.py
```

## Results Summary

The evaluation results demonstrate that TrustMed AI:
- Provides highly relevant answers to medical queries
- Retrieves contextually appropriate source material
- Grounds responses in authoritative medical content
- Maintains transparency through citation of sources

