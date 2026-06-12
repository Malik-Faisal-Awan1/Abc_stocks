<div align="center">

# ABC Stocks Dashboard

**A minimalist, AI-powered financial dashboard.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E.svg?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)

</div>

---

## ⚡ Overview

ABC Stocks Dashboard is a premium financial analysis tool combining traditional technical indicators with modern Machine Learning techniques. It features a completely custom, ultra-minimalist dark UI utilizing glassmorphism and modern web typography.

### Core Features
*   **Technical Analysis:** Computes RSI, MACD, and a proprietary Composite Momentum Score.
*   **Backtesting Engine:** Replays signal logic over the last 90 trading days to compute hypothetical hit-rates and portfolio curves.
*   **Machine Learning Insights:**
    *   **Signal Confidence:** Logistic Regression models trained on the fly using session data to predict the reliability of current trading signals.
    *   **Anomaly Detection:** Unsupervised Isolation Forests flagging statistically unusual trading days based on price/volume action.
*   **Local Data Ingestion:** Downloads real OHLCV market data via `yfinance` to operate completely offline without restrictive paid API limits.

---

## 🚀 Quick Start

Follow these steps to get the dashboard running locally on any machine.

### 1. Clone the Repository
```bash
git clone https://github.com/Malik-Faisal-Awan1/Abc_stocks.git
cd Abc_stocks
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
The app requires an `.env` file to configure its run mode.
```bash
# Copy the example file
cp .env.example .env

# Ensure USE_MOCK=true is set in the .env file to use local data
```

### 5. Download Local Market Data
Because premium APIs can be restrictive, the app fetches historical data directly from Yahoo Finance and saves it locally.
```bash
python scripts/download_local_data.py
```
*(This will fetch 180 days of accurate data for 15 major tickers like AAPL, MSFT, NVDA, TSLA, etc.)*

### 6. Launch the Dashboard
```bash
streamlit run app/streamlit_app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing

The codebase maintains strict reliability with a full Pytest suite. To verify the integrity of the data fetching, backtesting, and ML engines:

```bash
pytest tests/ -v --ignore=tests/test_integration.py
```

---

<div align="center">
  <i>Designed with precision.</i>
</div>
