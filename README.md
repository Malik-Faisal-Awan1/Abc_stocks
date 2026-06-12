# ABC Stocks Dashboard

A single-asset financial analytics dashboard in Streamlit that outputs probabilistic directional classifications for equities, backed by technical indicators and pre-scored sentiment data.

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment:
   Copy `.env.example` to `.env` and fill in your Finnhub API key.

3. Run the app:
   ```bash
   streamlit run app/streamlit_app.py
   ```

## Mock Mode vs Live Mode
By default, the app runs in **Mock Mode** using local static JSON files to prevent exhausting API limits during development. 

To enable live fetching from the Finnhub API without modifying `config.py`, run with the environment variable override:
```bash
USE_MOCK=false streamlit run app/streamlit_app.py
```
Or set `USE_MOCK=false` in your `.env` file.

## Integration Tests
Integration tests run against the live Finnhub API and cost API quota. They are skipped by default.
To run integration tests:
```bash
RUN_INTEGRATION=true pytest tests/test_integration.py -v
```

## Architecture Overview
- `app/`: Presentation layer (Streamlit). No business logic.
- `src/`: Data fetching, indicators calculation, and sentiment parsing. No Streamlit imports.
- `tests/`: Pytest suite for unit testing `src` components.
- `data/`: Mock data files and runtime caching.

## Disclaimer
This is a decision-support tool, not a trading signal generator. Past performance does not guarantee future results.

---

## Phase 3 — ML + Dark Theme (2026-06-13)

### New Features
- **Anomaly Detection** (`src/anomaly_detector.py`): Isolation Forest trained on daily OHLCV features flags statistically unusual trading days with orange triangle markers on the price chart.
- **Signal Classifier** (`src/ml_classifier.py`): Logistic Regression trained on backtesting signal_log predicts whether the current signal is likely correct. Confidence % displayed in Tab 1.
- **ML Insights Tab** (Tab 3): Feature importance bar chart, anomaly date table, and methodology note always visible.
- **Dark Theme**: Financial dark palette via `.streamlit/config.toml` and consistent `CHART_TEMPLATE` across all Plotly charts.

### Phase 3 Setup
```bash
pip install -r requirements.txt   # now includes scikit-learn>=1.4.0 and joblib>=1.3.0
streamlit run app/streamlit_app.py
```

### Running Tests
```bash
# Windows — set your API key then run:
$env:FINNHUB_API_KEY="your_key_here"
python -m pytest tests/ -v --ignore=tests/test_integration.py
# Expected: 48 passed, 0 failed
```

### ML Model Notes
- Models train fresh each session per ticker. Saved to `models/<TICKER>_classifier.pkl` (gitignored).
- Minimum 20 non-neutral signals required for classifier training. Falls back gracefully.
- All accuracy figures have high variance at 57–80 samples — stated in the UI.
- These are educational demonstrations, not production trading signals.
