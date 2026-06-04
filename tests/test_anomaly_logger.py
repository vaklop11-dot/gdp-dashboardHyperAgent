import os
from anomaly_logger import log_anomaly, LOG_PATH


def test_log_anomaly(tmp_path, monkeypatch):
    # Redirect log path to temporary file
    monkeypatch.setattr('anomaly_logger.LOG_PATH', tmp_path / 'anomaly_log.jsonl')
    aid = log_anomaly('Minor', 'Test description', 'root', 'fix', verified_by='tester')
    assert aid.startswith('ANM-')
    assert (tmp_path / 'anomaly_log.jsonl').exists()
    content = (tmp_path / 'anomaly_log.jsonl').read_text(encoding='utf-8')
    assert 'Test description' in content
