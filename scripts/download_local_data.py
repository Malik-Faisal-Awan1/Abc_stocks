import yfinance as yf
import json
from pathlib import Path
from datetime import datetime, timedelta

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "TSLA", "NVDA", "NFLX", "JPM", "V",
    "WMT", "UNH", "HD", "PG", "DIS"
]

def download_data():
    mock_dir = Path(__file__).parent.parent / "data" / "mock"
    mock_dir.mkdir(parents=True, exist_ok=True)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180) # Grab 180 days to ensure we have enough trading days
    
    print(f"Downloading data for {len(TICKERS)} tickers...")
    
    for ticker in TICKERS:
        try:
            print(f"Fetching {ticker}...")
            # Use interval="1d"
            df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), progress=False)
            
            if df.empty:
                print(f"Warning: No data for {ticker}")
                continue
                
            # yfinance returns multi-index columns in recent versions if not careful, 
            # but for a single ticker it should be single-level or easily flattened.
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten multi-index
                df.columns = [col[0] for col in df.columns]
                
            # Finnhub format
            data = {
                "s": "ok",
                "t": [int(x.timestamp()) for x in df.index],
                "o": df["Open"].tolist(),
                "h": df["High"].tolist(),
                "l": df["Low"].tolist(),
                "c": df["Close"].tolist(),
                "v": df["Volume"].tolist()
            }
            
            out_path = mock_dir / f"mock_ohlcv_{ticker}.json"
            with open(out_path, "w") as f:
                json.dump(data, f)
            print(f"Saved {out_path.name}")
            
        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}")

if __name__ == "__main__":
    # need pandas for MultiIndex check
    import pandas as pd
    download_data()
    print("Done!")
