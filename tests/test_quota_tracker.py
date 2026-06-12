import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from src.quota_tracker import QuotaTracker
import config

def test_record_call_increments_count():
    tracker = QuotaTracker()
    tracker.record_call()
    tracker.record_call()
    tracker.record_call()
    assert tracker.calls_in_last_minute() == 3

@patch('src.quota_tracker.datetime')
def test_old_calls_purged(mock_dt):
    tracker = QuotaTracker()
    
    # Mock time at T=0
    base_time = datetime(2026, 1, 1, 12, 0, 0)
    mock_dt.now.return_value = base_time
    tracker.record_call()
    
    # Move time forward 65 seconds
    mock_dt.now.return_value = base_time + timedelta(seconds=65)
    
    assert tracker.calls_in_last_minute() == 0

@patch('src.quota_tracker.datetime')
def test_near_limit_flag(mock_dt):
    tracker = QuotaTracker()
    base_time = datetime(2026, 1, 1, 12, 0, 0)
    mock_dt.now.return_value = base_time
    
    for _ in range(55):
        tracker.record_call()
        
    assert tracker.is_near_limit() is True
