# LangSmith Integration for Offline Evaluation

This guide covers how to use LangSmith for evaluating and tracking SPIN scoring performance with custom metrics (Pearson r, QWK, ±1 accuracy).

## Overview

LangSmith provides:
- **Dataset Management**: Store ground truth data centrally
- **Experiment Tracking**: Version and compare evaluation runs
- **Web UI**: Visualize metrics and analyze results
- **Custom Evaluators**: Reuse your existing metrics (Pearson r, QWK, ±1 accuracy)

## Quick Start

### 1. Setup LangSmith Account

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Get your API key from Settings
3. Add to your `.env` file:

```bash
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=spin-scoring  # optional, defaults to "default"
```

### 2. Install Dependencies

```bash
# Already added to requirements.txt
pip install langsmith>=0.2.0
```

Or rebuild Docker:

```bash
docker-compose build
```

### 3. Upload Your Evaluation Dataset

Convert your CSV file to a LangSmith dataset:

```bash
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv app/eval/sample_eval_data.csv \
  --dataset-name sales-eval-v1 \
  --description "Initial evaluation set with 10 examples"
```

**CSV Format** (same as offline evaluation):
```csv
id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hi\\nBuyer: Hello",4,3,4,3,4,4,3
```

### 4. Run Evaluation

```bash
docker-compose run --no-deps --rm -e MOCK_LLM=true app python -m app.eval.run_langsmith \
  --dataset sales-eval-v1 \
  --experiment baseline-v1 \
  --description "Baseline prompt with SPIN examples"
```

### 5. View Results

Open [https://smith.langchain.com](https://smith.langchain.com) and navigate to your project. You'll see:
- Per-example metrics (exact match, distance, within ±1)
- Aggregate metrics (Pearson r, QWK, ±1 accuracy per dimension)
- Macro averages across all dimensions

## Architecture: Two Evaluation Paths

### Path 1: CSV-Based (Existing)

**File**: [`app/eval/run.py`](run.py)

```bash
docker-compose run --no-deps --rm app python -m app.eval.run \
  --input data.csv --output report.json
```

**Pros**:
- Simple, self-contained
- No external dependencies
- Good for CI/CD
- Fast iteration

**Cons**:
- Manual report management
- No visualization
- Difficult to compare runs

### Path 2: LangSmith-Based (New)

**File**: [`app/eval/run_langsmith.py`](run_langsmith.py)

```bash
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-eval-v1 --experiment prompt-v2
```

**Pros**:
- Automatic experiment tracking
- Web UI for visualization
- Easy comparison of prompt versions
- Team collaboration
- Dataset versioning

**Cons**:
- Requires LangSmith account
- API key management
- Depends on external service

## Recommended Workflow

Use **both** approaches:

1. **Development**: Use CSV-based for quick iterations
2. **Milestones**: Use LangSmith for tracking major prompt versions
3. **CI/CD**: Use CSV-based for automated checks
4. **Stakeholder Reviews**: Use LangSmith web UI for demos

## Custom Evaluators Explained

### Row-Level Evaluators

Applied to each example individually:

- **`{dimension}_exact_match`**: 1 if prediction exactly matches ground truth, else 0
- **`{dimension}_within_one`**: 1 if prediction within ±1 of ground truth, else 0
- **`{dimension}_distance`**: Absolute distance between prediction and ground truth
- **`overall_quality`**: Average quality across all dimensions (1.0 = perfect, 0.0 = worst)

Example output for one example:
```python
{
  "situation_exact_match": 1.0,
  "situation_within_one": 1.0,
  "situation_distance": 0.0,
  "problem_exact_match": 0.0,
  "problem_within_one": 1.0,
  "problem_distance": 1.0,
  ...
  "overall_quality": 0.89
}
```

### Summary Evaluators

Applied to entire dataset (computed once per evaluation):

- **`{dimension}_pearson_r`**: Pearson correlation coefficient (-1 to 1)
- **`{dimension}_qwk`**: Quadratic Weighted Kappa (-1 to 1)
- **`{dimension}_plus_minus_one_accuracy`**: Fraction within ±1 (0 to 1)
- **`macro_avg_pearson_r`**: Average Pearson r across all dimensions
- **`macro_avg_qwk`**: Average QWK across all dimensions
- **`macro_avg_plus_minus_one_accuracy`**: Average ±1 accuracy across all dimensions

Example output:
```python
{
  "situation_pearson_r": 0.85,
  "situation_qwk": 0.82,
  "situation_plus_minus_one_accuracy": 0.95,
  ...
  "macro_avg_pearson_r": 0.83,
  "macro_avg_qwk": 0.81,
  "macro_avg_plus_minus_one_accuracy": 0.93
}
```

## Common Use Cases

### 1. Baseline Evaluation

Establish baseline performance with your initial prompt:

```bash
# Upload dataset (one time)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/gold_set.csv \
  --dataset-name sales-gold-set

# Run baseline
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment baseline \
  --description "Initial SPIN prompt with basic examples"
```

### 2. Iterate on Prompts

After modifying your prompt templates:

```bash
# Edit app/prompts/prompt_templates.py

# Run evaluation with new experiment name
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment prompt-v2-more-examples \
  --description "Added 3 more implication question examples"
```

### 3. Compare Experiments

In LangSmith web UI:
1. Go to "Datasets"
2. Click your dataset name
3. Go to "Experiments" tab
4. Select 2+ experiments to compare side-by-side
5. Sort by macro_avg_qwk to see which prompt performs best

### 4. Analyze Weak Dimensions

If a dimension consistently underperforms:

```bash
# Run evaluation
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment analyze-weak-dims

# In web UI:
# - Filter by dimension metrics (e.g., "implication_pearson_r")
# - Sort examples by distance
# - Review examples where model performs poorly
# - Adjust prompt with better examples for that dimension
```

### 5. Model Comparison

Compare different LLM models:

```bash
# Set model in .env or pass as environment variable
export MODEL_NAME=gpt-4o-mini
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment gpt-4o-mini-baseline

export MODEL_NAME=gpt-4o
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment gpt-4o-baseline
```

## Advanced Features

### Dataset Versioning

Create multiple dataset versions for different test sets:

```bash
# Development set (fast iteration)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/dev_set_50.csv \
  --dataset-name sales-dev-set

# Validation set (checkpoint)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/val_set_100.csv \
  --dataset-name sales-val-set

# Gold set (final evaluation)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/gold_set_200.csv \
  --dataset-name sales-gold-set
```

### Updating Datasets

Add new examples to existing dataset:

```bash
# Append mode (default)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/new_examples.csv \
  --dataset-name sales-gold-set

# Overwrite mode (replace entire dataset)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/updated_gold_set.csv \
  --dataset-name sales-gold-set \
  --overwrite
```

### Fast Evaluation (Summary Only)

Skip per-example metrics for faster evaluation:

```bash
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment quick-check \
  --no-row-evaluators
```

### Tracing Integration (Optional)

Enable LangSmith tracing to see individual LLM calls:

```bash
# Add to .env
LANGCHAIN_TRACING_V2=true

# Now evaluations will also trace scorer calls
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-set \
  --experiment traced-eval
```

View traces in LangSmith UI under "Tracing" tab.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Evaluate Prompt Changes

on:
  pull_request:
    paths:
      - 'app/prompts/**'

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Evaluation
        env:
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
          MOCK_LLM: "false"  # Use real LLM in CI
        run: |
          docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
            --dataset sales-ci-set \
            --experiment pr-${{ github.event.pull_request.number }} \
            --description "PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}"

      - name: Comment PR with Results
        run: |
          # Fetch results from LangSmith API and post to PR
          # (Implementation depends on your workflow)
```

### Quality Gate

Fail CI if metrics drop below threshold:

```bash
#!/bin/bash
# ci/eval_gate.sh

# Run evaluation
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-ci-set \
  --experiment ci-check \
  > eval_output.txt

# Parse macro_avg_qwk from output (or query LangSmith API)
QWK=$(grep "macro_avg_qwk" eval_output.txt | awk '{print $2}')

# Fail if below threshold
if (( $(echo "$QWK < 0.75" | bc -l) )); then
  echo "❌ QWK below threshold: $QWK < 0.75"
  exit 1
fi

echo "✅ QWK passed threshold: $QWK >= 0.75"
```

## Troubleshooting

### Error: "LANGCHAIN_API_KEY not set"

**Solution**: Add API key to `.env` file:
```bash
LANGCHAIN_API_KEY=your_key_here
```

Or pass directly:
```bash
docker-compose run --no-deps --rm -e LANGCHAIN_API_KEY=your_key app python -m app.eval.run_langsmith ...
```

### Error: "Dataset not found"

**Solution**: Upload dataset first:
```bash
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data.csv --dataset-name your-dataset-name
```

### Error: "langsmith package not installed"

**Solution**: Rebuild Docker image:
```bash
docker-compose build
```

Or install manually:
```bash
docker-compose run --no-deps --rm app pip install langsmith>=0.2.0
```

### Low Correlation Despite Good Visual Results

**Issue**: Pearson r is low even though predictions look good.

**Explanation**: Pearson r measures **linear** correlation. If:
- Ground truth has little variance (all 3s and 4s)
- Predictions are consistently off by a constant (e.g., always +1)
- Dataset is too small (< 20 examples)

Then correlation may be misleading.

**Solution**: Focus on:
- QWK (more robust for ordinal data)
- ±1 accuracy (practical measure)
- Increase dataset size

### Negative Pearson r or QWK

**Issue**: Metrics are negative.

**Explanation**:
- **Pearson r < 0**: Inverse correlation (model predicts opposite direction)
- **QWK < 0**: Worse than random agreement

**Solution**: Review prompt rubric to ensure it aligns with ground truth definitions.

## Comparison: CSV-based vs LangSmith

| Feature | CSV-based (`run.py`) | LangSmith (`run_langsmith.py`) |
|---------|---------------------|-------------------------------|
| **Setup** | None | API key required |
| **Storage** | Local JSON files | Cloud (LangSmith) |
| **Visualization** | Manual (jq, Python) | Web UI |
| **Experiment Tracking** | Manual file naming | Automatic versioning |
| **Comparison** | Manual JSON diff | Side-by-side in UI |
| **Team Sharing** | Share JSON files | Share URL |
| **CI/CD** | Easy | Requires API key |
| **Speed** | Fast | Slightly slower (API calls) |
| **Cost** | Free | Free tier: 5k traces/month |

## Best Practices

### 1. Dataset Quality

- **Size**: 50-100 examples minimum for reliable metrics
- **Diversity**: Include range of scores (1-5) and conversation types
- **Quality**: Multiple raters, resolve disagreements
- **Splits**: Separate dev/val/test sets

### 2. Experiment Naming

Use descriptive experiment names:

✅ Good:
- `baseline-gpt4o-mini`
- `v2-added-implication-examples`
- `v3-improved-rubric-clarity`

❌ Bad:
- `test1`
- `experiment`
- `eval_2025_11_06`

### 3. Iteration Workflow

1. **Baseline**: Establish initial performance
2. **Hypothesis**: Identify weak dimension (e.g., "implication")
3. **Change**: Modify prompt with more examples
4. **Evaluate**: Run with new experiment name
5. **Compare**: View side-by-side in LangSmith
6. **Decide**: Keep change if metrics improve

### 4. Metrics Interpretation

**Primary**: Focus on QWK (most robust for 1-5 ordinal scores)
- QWK > 0.8: Excellent agreement
- QWK 0.6-0.8: Substantial agreement
- QWK < 0.6: Needs improvement

**Secondary**: Use Pearson r for trend analysis
- Track if correlation improves over prompt iterations

**Practical**: Use ±1 accuracy for stakeholder communication
- "92% of predictions within 1 point" is easier to understand than "QWK = 0.78"

### 5. When to Use Each Approach

**Use CSV-based** for:
- Quick local iteration
- CI/CD automated checks
- No internet connection
- Sensitive data (air-gapped environment)

**Use LangSmith** for:
- Tracking prompt evolution over time
- Comparing multiple model/prompt combinations
- Team collaboration and review
- Stakeholder demos

## Example: Complete Calibration Loop

```bash
# 1. Initial setup (one time)
docker-compose run --no-deps --rm app python -m app.eval.upload_dataset \
  --csv data/gold_set_100.csv \
  --dataset-name sales-gold-100

# 2. Baseline evaluation
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-100 \
  --experiment baseline

# Output:
#   macro_avg_pearson_r: 0.68
#   macro_avg_qwk: 0.62
#   macro_avg_plus_minus_one_accuracy: 0.88

# 3. Analyze in web UI
# - Navigate to https://smith.langchain.com
# - Click dataset "sales-gold-100"
# - View "baseline" experiment
# - Sort by "implication_qwk" → see it's lowest (0.48)

# 4. Improve implication examples in prompt
# Edit: app/prompts/prompt_templates.py
# Add 3 more implication question examples

# 5. Re-evaluate
docker-compose run --no-deps --rm app python -m app.eval.run_langsmith \
  --dataset sales-gold-100 \
  --experiment v2-implication-examples \
  --description "Added 3 implication examples"

# Output:
#   macro_avg_pearson_r: 0.75  (+0.07)
#   macro_avg_qwk: 0.71        (+0.09)
#   macro_avg_plus_minus_one_accuracy: 0.92 (+0.04)
#   implication_qwk: 0.65      (+0.17 - significant improvement!)

# 6. Compare in UI
# - Go to "Experiments" tab
# - Select "baseline" and "v2-implication-examples"
# - Click "Compare"
# - See improvements across all dimensions, especially implication

# 7. Deploy new prompt
# Merge PR with updated prompt_templates.py
```

## References

- **LangSmith Docs**: https://docs.smith.langchain.com
- **LangSmith API**: https://smith.langchain.com/settings
- **Custom Evaluators Guide**: https://docs.langchain.com/langsmith/code-evaluator
- **Offline Evaluation README**: [README.md](README.md)
- **Metrics Module**: [metrics.py](metrics.py)
- **LangSmith Evaluators**: [langsmith_evaluators.py](langsmith_evaluators.py)
