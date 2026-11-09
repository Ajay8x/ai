# Feature Specification: Intent Catalog Merge and Boundary Routing

Status: FINALIZED

## User goal

Keep the useful intent coverage while merging overlapping natural-language categories and preventing broad rules from stealing specialized requests.

## Requirements

1. Merge only clearly overlapping content/workflow categories; preserve unique system, RAG, network, calculation, and safety intents.
2. Load the merged catalog consistently for cosine matching, neural training, diagnostics, and settings telemetry.
3. Add deterministic boundaries for the previously observed collisions: website vs application, memory recall vs save, specialized calculations vs generic calculation, QR/HTML/CSS/test generation vs generic code, and network testing.
4. Keep Hindi, Hinglish, and English sample phrases available after merging.
5. Verify every active intent with a representative question and regression-test the boundary cases.

## Acceptance criteria

- The runtime catalog contains the merged count and the neural checkpoint metadata matches it.
- All merged target intents retain the source patterns without duplicates.
- The eight observed collision families route to the intended specialized intent for representative natural questions.
- The full focused test suite passes and the 100-intent validation is replaced by validation for every active merged intent.
