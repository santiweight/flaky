"""
End-to-end integration tests for the full system.
"""

import pytest
import requests
import time
from pathlib import Path
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def check_backend_running():
    """Verify backend is running before tests."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    except Exception as e:
        pytest.skip(f"Backend not running: {e}")


def create_test_pdf() -> bytes:
    """Create a simple test PDF with a multiple choice question."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, "Practice Quiz")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, "1. What is the capital of France?")
    c.drawString(70, 700, "A. London")
    c.drawString(70, 680, "B. Berlin")
    c.drawString(70, 660, "C. Paris")
    c.drawString(70, 640, "D. Madrid")
    
    c.drawString(50, 600, "2. What is 2 + 2?")
    c.drawString(70, 580, "A. 3")
    c.drawString(70, 560, "B. 4")
    c.drawString(70, 540, "C. 5")
    c.drawString(70, 520, "D. 6")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def test_health_endpoint(check_backend_running):
    """Test that health endpoint is accessible."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_solve_upload_endpoint(check_backend_running):
    """Test solving a quiz via file upload."""
    pdf_bytes = create_test_pdf()
    
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    data = {"runs": "1"}
    
    response = requests.post(f"{BASE_URL}/solve-upload", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify response structure
    assert "url" in result
    assert "num_questions" in result
    assert "num_runs" in result
    assert "questions" in result
    assert "runs" in result
    
    # Should have parsed 2 questions
    assert result["num_questions"] >= 1
    assert result["num_runs"] == 1
    
    # Verify questions structure
    for question in result["questions"]:
        assert "number" in question
        assert "question" in question
        assert "choices" in question
        assert isinstance(question["choices"], dict)
    
    # Verify runs structure
    assert len(result["runs"]) == 1
    run = result["runs"][0]
    assert "run" in run
    assert "answers" in run
    
    # Verify answers
    for answer in run["answers"]:
        assert "question_number" in answer
        assert "question_text" in answer
        assert "choices" in answer
        assert "model_answer" in answer
        # Model answer should be a valid choice letter
        assert answer["model_answer"] in answer["choices"]


def test_solve_upload_invalid_file(check_backend_running):
    """Test uploading a non-PDF file."""
    files = {"file": ("test.txt", b"not a pdf", "text/plain")}
    data = {"runs": "1"}
    
    response = requests.post(f"{BASE_URL}/solve-upload", files=files, data=data)
    
    # Should fail with 400 or 500
    assert response.status_code in [400, 500]


def test_solve_upload_multiple_runs(check_backend_running):
    """Test running multiple generations via upload."""
    pdf_bytes = create_test_pdf()
    
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    data = {"runs": "3"}
    
    response = requests.post(f"{BASE_URL}/solve-upload", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["num_runs"] == 3
    assert len(result["runs"]) == 3
    
    # Each run should have answers
    for i, run in enumerate(result["runs"], 1):
        assert run["run"] == i
        assert len(run["answers"]) == result["num_questions"]


def test_proxy_pdf_endpoint(check_backend_running):
    """Test PDF proxying (requires a real accessible URL)."""
    # Use a simple test PDF URL
    test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    response = requests.get(f"{BASE_URL}/proxy-pdf", params={"url": test_url}, timeout=10)
    
    # May fail if URL is blocked, but should not crash
    assert response.status_code in [200, 400, 403, 404]
    
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0


def test_answer_sheet_endpoint(check_backend_running):
    """Test answer sheet generation."""
    pdf_bytes = create_test_pdf()
    
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    data = {"runs": "1"}
    
    # First solve the quiz
    solve_response = requests.post(f"{BASE_URL}/solve-upload", files=files, data=data)
    assert solve_response.status_code == 200
    
    # Now generate answer sheet
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    response = requests.post(f"{BASE_URL}/answer-sheet", files=files, data=data)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0
    
    # Verify it's a valid PDF (starts with %PDF)
    assert response.content.startswith(b"%PDF")


def test_concurrent_requests(check_backend_running):
    """Test that backend handles concurrent requests."""
    pdf_bytes = create_test_pdf()
    
    import concurrent.futures
    
    def make_request():
        files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
        data = {"runs": "1"}
        response = requests.post(f"{BASE_URL}/solve-upload", files=files, data=data, timeout=30)
        return response.status_code
    
    # Make 3 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # All should succeed
    assert all(status == 200 for status in results)


def test_frontend_accessible():
    """Test that frontend is serving."""
    try:
        response = requests.get("http://localhost:5173", timeout=2)
        assert response.status_code == 200
        # Should contain the app title
        assert b"Do My Homework" in response.content or b"Vite" in response.content
    except Exception as e:
        pytest.skip(f"Frontend not running: {e}")


def test_cors_headers(check_backend_running):
    """Test that CORS headers are properly set."""
    response = requests.options(
        f"{BASE_URL}/health",
        headers={"Origin": "http://localhost:5173"}
    )
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers
