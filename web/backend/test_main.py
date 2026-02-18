"""
Unit tests for the backend API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io

from main import app, extract_text_from_pdf, parse_questions_with_llm, answer_question, Question


client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_text_from_pdf():
    """Test PDF text extraction."""
    # Create a minimal valid PDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Test question 1")
    c.drawString(100, 730, "A. Answer A")
    c.drawString(100, 710, "B. Answer B")
    c.save()
    
    pdf_bytes = buffer.getvalue()
    text = extract_text_from_pdf(pdf_bytes)
    
    assert "Test question 1" in text
    assert "Answer A" in text


@patch('main.client')
def test_parse_questions_with_llm(mock_client):
    """Test question parsing with mocked LLM."""
    mock_response = Mock()
    mock_response.content = [Mock(text='[{"number": 1, "question": "Test?", "choices": {"A": "Yes", "B": "No"}}]')]
    mock_client.messages.create.return_value = mock_response
    
    text = "1. Test? A. Yes B. No"
    questions = parse_questions_with_llm(text)
    
    assert len(questions) == 1
    assert questions[0].number == 1
    assert questions[0].question == "Test?"
    assert "A" in questions[0].choices


@patch('main.client')
def test_answer_question(mock_client):
    """Test question answering with mocked LLM."""
    mock_response = Mock()
    mock_response.content = [Mock(text='A')]
    mock_client.messages.create.return_value = mock_response
    
    question = Question(
        number=1,
        question="What is 2+2?",
        choices={"A": "4", "B": "5", "C": "6", "D": "7"}
    )
    
    answer = answer_question(question)
    assert answer == "A"


@patch('main.download_pdf')
@patch('main.extract_text_from_pdf')
@patch('main.parse_questions_with_llm')
@patch('main.answer_question')
def test_solve_endpoint(mock_answer, mock_parse, mock_extract, mock_download):
    """Test the /solve endpoint with all dependencies mocked."""
    mock_download.return_value = b"fake pdf"
    mock_extract.return_value = "fake text"
    mock_parse.return_value = [
        Question(number=1, question="Q1?", choices={"A": "1", "B": "2"}),
        Question(number=2, question="Q2?", choices={"A": "3", "B": "4"}),
    ]
    mock_answer.side_effect = ["A", "B"]
    
    response = client.post("/solve", json={"url": "http://test.com/test.pdf", "runs": 1})
    
    assert response.status_code == 200
    data = response.json()
    assert data["num_questions"] == 2
    assert data["num_runs"] == 1
    assert len(data["questions"]) == 2
    assert len(data["runs"]) == 1
    assert len(data["runs"][0]["answers"]) == 2
    assert data["runs"][0]["answers"][0]["model_answer"] == "A"
    assert data["runs"][0]["answers"][1]["model_answer"] == "B"


def test_solve_endpoint_missing_url():
    """Test /solve endpoint with missing URL."""
    response = client.post("/solve", json={"runs": 1})
    assert response.status_code == 422


@patch('main.download_pdf')
def test_solve_endpoint_download_failure(mock_download):
    """Test /solve endpoint when PDF download fails."""
    mock_download.side_effect = Exception("Network error")
    
    response = client.post("/solve", json={"url": "http://bad.com/test.pdf", "runs": 1})
    assert response.status_code == 400
    assert "Failed to download PDF" in response.json()["detail"]


@patch('main.download_pdf')
def test_proxy_pdf_endpoint(mock_download):
    """Test the /proxy-pdf endpoint."""
    mock_download.return_value = b"fake pdf content"
    
    response = client.get("/proxy-pdf?url=http://test.com/test.pdf")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"fake pdf content"


def test_proxy_pdf_missing_url():
    """Test /proxy-pdf endpoint without URL parameter."""
    response = client.get("/proxy-pdf")
    assert response.status_code == 422
