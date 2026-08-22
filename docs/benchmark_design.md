# Benchmark design principles

## Evaluation separation

Planner output is only an artifact. Metrics are recomputed by validators.

## Metric layers

1. Feasibility:
   - inside boundary
   - collision free
   - coverage constraints

2. Benchmark comparison:
   - path length
   - swath count
   - planning time
   - remaining area

3. Agricultural quality:
   - overlap ratio
   - non-work distance

## Scope

Block A targets reproducible 2D agricultural coverage planning experiments.
It intentionally does not model robot dynamics.
