def parse_sentiment(sentiment_response: dict, news_response: list) -> dict:
    
    try:
        bullish_pct = sentiment_response.get("sentiment", {}).get("bullishPercent", None)
        bearish_pct = sentiment_response.get("sentiment", {}).get("bearishPercent", None)
        score = sentiment_response.get("companyNewsScore", None)
        article_count = len(news_response) if news_response else 0

        if bullish_pct is None or score is None:
            return {"is_valid": False, "reason": "Sentiment data unavailable for this ticker"}

        label = "Bullish" if bullish_pct > 0.5 else "Bearish" if bearish_pct > 0.5 else "Neutral"

        return {
            "is_valid": True,
            "label": label,
            "bullish_pct": round(bullish_pct * 100, 1),
            "bearish_pct": round(bearish_pct * 100, 1),
            "company_news_score": round(score, 3),
            "article_count": article_count,
            "attribution": "Sentiment scored by Finnhub. Methodology not independently verified."
        }
    except Exception:
        return {"is_valid": False, "reason": "Sentiment parsing failed"}
