def test_comeback_ci_smoke_imports():
    from app.comeback_detector import ComebackDetector
    from app.comeback_quality import evaluate_candidate_quality
    from app.comeback_scanner import ComebackScanner

    assert ComebackDetector is not None
    assert ComebackScanner is not None
    assert callable(evaluate_candidate_quality)
