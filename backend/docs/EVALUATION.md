# Offline Evaluation and Calibration

This module provides tools for evaluating LLM scorer performance against ground truth labels.

## Features

- **Metrics**: Pearson correlation (r), Quadratic Weighted Kappa (QWK), ±1 band accuracy
- **CLI Runner**: Process CSV files with ground truth labels and generate JSON reports
- **Per-Dimension Analysis**: Evaluate each scoring dimension independently
- **Macro Averages**: Overall performance across all dimensions
- **Efficient Single-Pass Scoring**: LLM scores each transcript only once, even when using LangSmith
- **Automatic LangSmith Integration**: Results automatically pushed to LangSmith cloud (if configured)

## Architecture: Efficient Single-Pass Evaluation

The evaluation system uses an efficient single-pass architecture that eliminates redundant LLM calls:

### How It Works

```
1. Score Transcripts (ONCE)
   ├─ Load CSV with ground truth
   ├─ For each transcript:
   │  └─ Call LLM scorer (expensive operation)
   └─ Collect all predictions
   
2. Compute Metrics (fast)
   ├─ Calculate Pearson r, QWK, ±1 accuracy
   └─ Compute macro averages
   
3. Store Locally (always)
   └─ Save to PostgreSQL database
   
4. Push to LangSmith (optional)
   └─ Upload pre-computed results (no re-scoring!)
```

### Cost Savings

**Traditional approach** (2x LLM calls per transcript):
- Local evaluation: 100 transcripts × 1 LLM call = 100 API calls
- LangSmith tracking: 100 transcripts × 1 LLM call = 100 API calls
- **Total: 200 API calls** 💸💸

**Efficient approach** (1x LLM call per transcript):
- Score once: 100 transcripts × 1 LLM call = 100 API calls
- Compute metrics locally (free)
- Push to LangSmith (no LLM calls, just result upload)
- **Total: 100 API calls** 💸

**Result: 50% cost reduction when using LangSmith!**

## Quick Start

### 1. Prepare Your Evaluation Data

Create a CSV file with ground truth labels. Required columns:

```csv
id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hi there\nBuyer: Hello",4,3,4,3,4,4,3
2,"Rep: How's business?\nBuyer: Good thanks",3,4,3,4,3,4,4
3,"Rep: Tell me about challenges\nBuyer: We need better tools",5,4,5,4,5,4,5
```

**Column Descriptions:**
- `id`: Unique identifier for each transcript
- `transcript`: Sales conversation text (use `\n` for line breaks)
- `score_situation`: Ground truth score (1-5) for Situation questions
- `score_problem`: Ground truth score (1-5) for Problem questions
- `score_implication`: Ground truth score (1-5) for Implication questions
- `score_need_payoff`: Ground truth score (1-5) for Need-Payoff questions
- `score_flow`: Ground truth score (1-5) for conversation flow
- `score_tone`: Ground truth score (1-5) for tone and professionalism
- `score_engagement`: Ground truth score (1-5) for customer engagement

### 2. Run Evaluation

Using Docker (recommended):

```bash
cd backend
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  --input /path/to/eval_data.csv \
  --output /path/to/report.json
```

Direct Python (requires environment setup):

```bash
python scripts/run_evaluation.py --input eval_data.csv --output report.json
```

### 3. Review Results

The evaluation produces a JSON report with:

```json
{
  "model_name": "gpt-4o-mini",
  "prompt_version": "spin_v1",
  "timestamp": "2025-11-06T12:30:00",
  "n_samples": 100,
  "per_dimension_metrics": {
    "situation": {
      "pearson_r": 0.85,
      "qwk": 0.82,
      "plus_minus_one_accuracy": 0.95
    },
    "problem": {
      "pearson_r": 0.83,
      "qwk": 0.80,
      "plus_minus_one_accuracy": 0.93
    }
  },
  "macro_averages": {
    "pearson_r": 0.83,
    "qwk": 0.81,
    "plus_minus_one_accuracy": 0.93
  }
}
```

## Metrics Explained

### Pearson Correlation (r)

Measures linear correlation between predictions and ground truth:
- **1.0**: Perfect positive correlation
- **0.0**: No correlation
- **-1.0**: Perfect negative correlation

**Interpretation**: Higher is better. Values > 0.7 indicate strong correlation.

### Quadratic Weighted Kappa (QWK)

Measures agreement between raters with quadratic weighting, penalizing larger disagreements more heavily:
- **1.0**: Perfect agreement
- **0.0**: Agreement expected by chance
- **< 0.0**: Worse than random

**Interpretation**:
- 0.0-0.20: Slight agreement
- 0.21-0.40: Fair agreement
- 0.41-0.60: Moderate agreement
- 0.61-0.80: Substantial agreement
- 0.81-1.00: Almost perfect agreement

### ±1 Band Accuracy

Fraction of predictions within ±1 of ground truth:
- **1.0**: All predictions exact or within 1
- **0.0**: No predictions within 1

**Interpretation**: For ordinal scoring (1-5), predictions off by 1 are often acceptable. Values > 0.85 indicate good calibration.

## Usage Examples

### Basic Evaluation

```bash
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  -i data/eval_set_v1.csv \
  -o results/report_2025-11-06.json
```

### Track Prompt Iterations

Run evaluation after each prompt change to track improvements:

```bash
# Baseline
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  -i data/eval_set.csv \
  -o results/baseline.json

# After prompt v2
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  -i data/eval_set.csv \
  -o results/prompt_v2.json

# Compare results
jq '.macro_averages' results/baseline.json results/prompt_v2.json
```

### CI/CD Integration

Add to your test pipeline:

```yaml
# .github/workflows/eval.yml
- name: Run evaluation
  run: |
    docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
      --input tests/fixtures/eval_gold_set.csv \
      --output eval_report.json

- name: Check QWK threshold
  run: |
    qwk=$(jq '.macro_averages.qwk' eval_report.json)
    if (( $(echo "$qwk < 0.6" | bc -l) )); then
      echo "QWK below threshold: $qwk"
      exit 1
    fi
```

## Development

### Running Tests

```bash
# Unit tests for metrics
docker-compose run --no-deps --rm app pytest tests/services/test_evaluation_metrics.py -v

# Smoke tests for evaluation pipeline
docker-compose run --no-deps --rm app pytest tests/services/test_evaluation_runner.py -v

# All evaluation tests
docker-compose run --no-deps --rm app pytest tests/services/test_evaluation_metrics.py tests/services/test_evaluation_runner.py -v
```

### Adding New Metrics

1. Add metric function to `app/services/evaluation_metrics.py`
2. Add tests to `tests/services/test_evaluation_metrics.py`
3. Update `compute_dimension_metrics()` in `app/services/evaluation_runner.py`
4. Update `compute_macro_averages()` to include new metric

## Best Practices

### Ground Truth Data

- **Size**: Aim for 50-100 samples minimum for reliable metrics
- **Diversity**: Include range of scores (1-5) and conversation types
- **Quality**: Have multiple human raters and resolve disagreements
- **Calibration Set**: Keep a separate gold set for calibration vs validation

### Evaluation Workflow

1. **Baseline**: Evaluate with initial prompt
2. **Iterate**: Modify prompt, re-evaluate
3. **Track**: Save reports with version tags
4. **Compare**: Use macro averages to compare versions
5. **Dimension Analysis**: Check per-dimension metrics to identify weak areas

### Interpretation

- **Focus on QWK**: Most robust for ordinal scores (1-5)
- **±1 Accuracy**: Good for practical calibration checks
- **Pearson r**: Useful for understanding linear relationships
- **Look at Patterns**: If one dimension consistently underperforms, adjust rubric or examples

## Example: Complete Calibration Loop

```bash
# 1. Create evaluation dataset (one-time)
# - Collect 100 diverse transcripts
# - Have expert raters score them
# - Save to data/eval_gold_set.csv

# 2. Baseline evaluation
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  -i data/eval_gold_set.csv \
  -o results/baseline_2025-11-06.json

# Output:
# Macro Averages:
#   Pearson r: 0.68
#   QWK: 0.62
#   ±1 Accuracy: 0.88

# 3. Analysis: "Implication" dimension is weak (r=0.55)
jq '.per_dimension_metrics.implication' results/baseline_2025-11-06.json

# 4. Iterate: Add more examples of implication questions to prompt
# Edit: app/prompts/prompt_templates.py

# 5. Re-evaluate
docker-compose run --no-deps --rm app python scripts/run_evaluation.py \
  -i data/eval_gold_set.csv \
  -o results/iteration_v2_2025-11-06.json

# Output:
# Macro Averages:
#   Pearson r: 0.75  (+0.07)
#   QWK: 0.71        (+0.09)
#   ±1 Accuracy: 0.92 (+0.04)

# 6. Compare improvements
echo "Baseline vs V2:"
jq -s '.[0].macro_averages, .[1].macro_averages' \
  results/baseline_2025-11-06.json \
  results/iteration_v2_2025-11-06.json
```

## Troubleshooting

### Low Correlation (r < 0.5)

- Check if prompt rubric aligns with ground truth definitions
- Verify ground truth quality (inter-rater agreement)
- Ensure model has enough context (longer prompts, more examples)

### Low QWK but Good ±1 Accuracy

- Model is close but systematically biased (e.g., always off by 1)
- Adjust calibration examples or scoring guidance

### Good Metrics on Dev Set, Poor on Production

- Overfitting to small eval set
- Collect more diverse ground truth data
- Use cross-validation or hold-out sets

## LangSmith Integration

The evaluation system automatically integrates with LangSmith when `LANGCHAIN_API_KEY` is configured.

### Automatic Integration (Web UI)

When you run evaluations through the web UI:
1. **Datasets auto-upload**: CSV datasets automatically sync to LangSmith
2. **Single-pass scoring**: Transcripts are scored once (no redundant LLM calls)
3. **Results pushed**: Pre-computed results uploaded to LangSmith
4. **URL stored**: LangSmith experiment URL saved in database

### How It's Different

**Old approach** (double scoring):
```python
# Phase 1: Score locally
for transcript in transcripts:
    local_score = llm.score(transcript)  # 💰 LLM API call

# Phase 2: Score for LangSmith
for transcript in transcripts:
    langsmith_score = llm.score(transcript)  # 💰 Redundant LLM API call!
```

**New approach** (single-pass):
```python
# Phase 1: Score ONCE
for transcript in transcripts:
    score = llm.score(transcript)  # 💰 Single LLM API call
    predictions.append(score)

# Phase 2: Compute metrics (fast, no LLM)
metrics = compute_metrics(predictions, ground_truth)

# Phase 3: Push to LangSmith (no LLM, just upload)
langsmith.push_results(predictions, metrics)
```

### Manual CLI Usage

For advanced features, see [LANGSMITH.md](LANGSMITH.md) for:
- Dataset management in LangSmith cloud
- Web UI for comparing prompt iterations
- Experiment versioning and tracking
- Custom evaluators using the same metrics

**CLI Commands**:
```bash
# Upload dataset
python scripts/upload_eval_dataset.py --csv data.csv --dataset-name my-eval

# Run evaluation
python scripts/run_langsmith_eval.py --dataset my-eval --experiment v1

# View results at https://smith.langchain.com
```

## References

- **Pearson Correlation**: Standard linear correlation measure
- **Cohen's Kappa**: Original agreement metric for categorical data
- **Quadratic Weighted Kappa**: Extension for ordinal data with distance-based penalties
  - Fleiss, J. L., & Cohen, J. (1973). "The equivalence of weighted kappa and the intraclass correlation coefficient"
- **±1 Band Accuracy**: Practical metric for ordinal classification in competitions like Kaggle
- **LangSmith Documentation**: https://docs.smith.langchain.com/
