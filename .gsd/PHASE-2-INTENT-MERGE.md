---
phase: 2
plan: 1
wave: 1
depends_on: []
files_modified:
  - ai/neural/dataset_loader.py
  - ai/neural/intent_classifier.py
  - training/gpu_train.py
  - models/ajax_neural_intent.pt
  - models/vocab_metadata.json
  - tests/test_intent_merge.py
autonomous: true

# Intent Merge Plan

## Objective

Reduce only overlapping intent categories and make specialized routing win over broad calculation/code/application rules.

## Tasks

1. Add one canonical merge map in the shared dataset loader and preserve all source patterns.
2. Add boundary guards and regression tests for the observed false-positive families.
3. Retrain the checkpoint from the merged loader and validate catalog/checkpoint parity plus representative coverage.

## Verification

- `python -m unittest tests.test_intent_merge tests.test_settings tests.test_chat_rag_upload -v`
- `python -m compileall -q ai/neural/dataset_loader.py ai/neural/intent_classifier.py training/gpu_train.py`
- Representative question coverage reports one result for every active merged intent.
