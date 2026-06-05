# N=9 → N=15 Expansion Summary

## 1. Models Added (OpenRouter)

| Model | OpenRouter ID | Notes |
|---|---|---|
| Claude Opus 4.8 | `anthropic/claude-opus-4.8` | |
| Claude Haiku | `anthropic/claude-haiku-4.5` | Versioned ID used (not latest alias) |
| Llama 3.1 8B Instruct | `meta-llama/llama-3.1-8b-instruct` | |
| Mistral Large | `mistralai/mistral-large` | |
| Cohere Command R+ | `cohere/command-r-plus-08-2024` | `cohere/command-r-plus` not found; versioned ID substituted |
| Kimi K2.6 | `moonshotai/kimi-k2.6` | Required `reasoning: {enabled: false}` for batch orientation |

## 2. Data Quality (6 New Models)

| Model | N | JSON% | Score% | NoRef% | StabSD | Flip% |
|---|---|---|---|---|---|---|
| Claude Haiku | 270 | 100.0 | 100.0 | 100.0 | 0.00 | 0.0 |
| Claude Opus 4.8 | 270 | 100.0 | 100.0 | 100.0 | 0.77 | 0.0 |
| Cohere Command R+ | 270 | 99.6 | 99.6 | 100.0 | 1.52 | 0.0 |
| Kimi K2.6 | 270 | 99.6 | 99.6 | 100.0 | 1.39 | 0.0 |
| Llama 3.1 8B Instruct | 270 | 100.0 | 100.0 | 100.0 | 0.28 | 0.0 |
| Mistral Large | 270 | 100.0 | 100.0 | 100.0 | 0.88 | 0.0 |

## 3. H1 Results: N=9 vs N=15

| | N=9 | N=15 |
|---|---|---|
| PVC β | +0.14 (p=0.96) | +1.51 (p=0.46) |
| CO β | +24.22 (p=0.009)** | +5.68 (p=0.12) |
| PVC sign stable (LOMO) | NO | NO |
| CO sign stable (LOMO) | YES | YES |
| PVC MDE (80%) | 6.8 | 5.25 |
| CO MDE (80%) | >10 | 9.25 |

**Key finding:** CO was significant at N=9 (p=0.009, R²=0.65) but becomes non-significant at N=15 (p=0.12, R²=0.17). The 6 new models dilute the CO-delta relationship. PVC remains null throughout.

## 4. H2 Results: N=9 vs N=15

| | N=9 | N=15 |
|---|---|---|
| PVC direct (c') | +1.17 (p≈0) | +1.55 (p<0.001) |
| PVC sign stable (LOMO) | NO | **YES** |
| collective β | -10.79*** | -6.20*** |
| access β | +12.93*** | +8.83*** |
| coercive β | +12.13*** | +6.02*** |
| Frame LOMO sign stable | YES (all) | YES (all) |
| a-paths significant | YES (all 3) | NO (all ns) |

**Key finding:** Frame coefficients remain highly significant and sign-stable at N=15. However, the a-paths (PVC→Frame) become non-significant, and indirect effects vanish. Frame effects on delta are robust; the mediation channel through PVC is not.

## 5. Overall Verdict

- **PVC remains null** as a predictor of mean_delta in bivariate models at both N=9 and N=15
- **CO loses significance** at N=15 — the strong N=9 finding was sensitive to sample composition
- **Frame effects on delta are robust** — collective, access, and coercive frames all remain significant and sign-stable
- **H3 was not re-run** per instructions
- **No models showed unusual behavior** — all Flip%=0, StabSD low, JSON validity >99.5%

## 6. Output Files

All expanded outputs under `outputs/expanded15/` and `outputs/openrouter_expansion/`.
