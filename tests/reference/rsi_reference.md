# RSI Reference Dataset

This document provides a static dataset and expected Relative Strength Index (RSI) calculation using Wilder's smoothing (exponential with alpha = 1/period) for a 14-period window.

**Reference:** Wilder (1978).

### Static Dataset
```python
prices = [
    150.5, 150.36, 151.01, 152.53, 152.3, 152.06, 153.64, 154.41, 153.94, 154.48, 
    154.02, 153.55, 153.79, 151.88, 150.16, 149.59, 148.58, 148.89, 147.99, 146.57, 
    148.04, 147.81, 147.88, 146.46, 145.91, 146.02, 144.87, 145.25, 144.65, 144.36, 
    143.75, 145.61, 145.59, 144.53, 145.36, 144.14, 144.35, 142.39, 141.06, 141.25, 
    141.99, 142.16, 142.05, 141.75, 140.27, 139.55, 139.09, 140.15, 140.49, 138.73, 
    139.05, 138.67, 137.99, 138.6, 139.63, 140.56, 139.72, 139.41, 139.75, 140.72, 
    140.24, 140.06, 138.95, 137.75, 138.57, 139.92, 139.85, 140.85, 141.22, 140.57, 
    140.93, 142.47, 142.43, 144.0, 141.38, 142.2, 142.29, 141.99, 142.08, 140.09, 
    139.87, 140.23, 141.71, 141.19, 140.38, 139.88, 140.8, 141.12, 140.59, 141.11
]
```

### Expected RSI Calculation (14-period)
Using Wilder's smoothing method, the expected RSI value on the final day (141.11) should be approximately **50.74**.
(Note: Exact value might vary slightly based on floating point precision, check tests/test_indicators.py for the exact tolerance).

The first 14 periods are used to establish the initial average gain and average loss.
The remaining periods exponentially smooth the gain and loss to provide an accurate RSI.
