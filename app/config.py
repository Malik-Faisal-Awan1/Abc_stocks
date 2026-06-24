import os
from dotenv import load_dotenv

load_dotenv()

def _get_api_key() -> str:
    """
    Supports both local .env and Streamlit Cloud secrets.toml.
    Import order: st.secrets first (cloud), os.getenv second (local).
    """
    try:
        import streamlit as st
        key = st.secrets.get("FINNHUB_API_KEY", None)
@@ -24,15 +20,13 @@ def _get_api_key() -> str:
        if key:
            return key
    except Exception:
        pass
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        raise EnvironmentError(
            "FINNHUB_API_KEY not set. "
            "Local: add to .env. "
            "Streamlit Cloud: add to Secrets in app settings."
        )
    return key

API_BASE_URL = "https://finnhub.io/api/v1"
PER_MINUTE_LIMIT = 60
BATCH_DELAY_SECONDS = 1
USE_MOCK = os.getenv("USE_MOCK", "true").lower() != "false"
CACHE_TTL_STANDARD = 3600   # 1 hour: OHLCV
CACHE_TTL_SENTIMENT = 1800  # 30 min: Sentiment

API_KEY: str = ""  # Populated at runtime via get_api_key()

def get_api_key() -> str:
    return _get_api_key()
