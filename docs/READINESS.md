# Readiness (Build 10)

Deterministic role readiness from recorded platform activity. **Not** a hiring probability.

## Sources & default weights

| Source | Weight |
|--------|--------|
| MCQ | 0.15 |
| Coding | 0.20 |
| SQL | 0.20 |
| Prompt | 0.15 |
| Scenario | 0.15 |
| Course | 0.05 |
| Project | 0.20 |
| Interview (self-review) | 0.10 |

Per-skill multipliers apply (e.g. SQL practice weighs more for SQL skill).

## Evidence strength

- **Low** (&lt;3 meaningful signals): effective score × 0.75
- **Medium** (3–7): × 0.90
- **High** (8+ or diverse sources): × 1.0

## Role readiness

Weighted sum of effective skill scores by role requirement importance (core 1.0, important 0.7, nice-to-have 0.4) × configured weight.

## Minimum evidence

Numeric role score shown only after ≥3 relevant activities.

## Recency

0–30d 100%, 31–90d 95%, 91–180d 90%, 180+d 85%.

## Backfill

```bash
python -m app.readiness.backfill
```
