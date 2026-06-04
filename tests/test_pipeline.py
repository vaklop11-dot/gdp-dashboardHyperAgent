from pipeline import HyperAgent


def test_hyperagent_runs():
    agent = HyperAgent()
    result = agent.solve('Simple test task for unit tests')
    assert hasattr(result, 'final_output')
    assert hasattr(result, 'audit')
    assert result.iterations >= 0
    assert result.verdict in ('PASS', 'FAIL')
