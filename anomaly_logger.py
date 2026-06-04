import json
from pathlib import Path
from datetime import datetime
import threading

_lock = threading.Lock()
LOG_PATH = Path(__file__).parents[0] / 'data' / 'anomaly_log.jsonl'
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _next_id():
    # Simple incremental ID based on existing entries
    if not LOG_PATH.exists():
        return 'ANM-001'
    with LOG_PATH.open('r', encoding='utf-8') as fh:
        count = sum(1 for _ in fh)
    return f'ANM-{count+1:03d}'


def log_anomaly(severity: str, description: str, root_cause: str, fix: str, verified_by: str = '') -> str:
    """Append an anomaly entry to the anomaly log and return the anomaly ID."""
    with _lock:
        aid = _next_id()
        entry = {
            'ID': aid,
            'Severity': severity,
            'Description': description,
            'Root Cause': root_cause,
            'Fix': fix,
            'Verified By': verified_by,
            'Date': datetime.utcnow().isoformat() + 'Z'
        }
        with LOG_PATH.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return aid
