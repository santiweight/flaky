from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import anthropic
import pdfplumber
import io
import json
from urllib.request import urlopen, Request
from typing import List, Dict, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic()

class SolveRequest(BaseModel):
    url: str
    runs: int = 1

class Question(BaseModel):
    number: int
    question: str
    choices: Dict[str, str]

class Answer(BaseModel):
    question_number: int
    question_text: str
    choices: Dict[str, str]
    model_answer: str

class Run(BaseModel):
    run: int
    answers: List[Answer]

class SolveResponse(BaseModel):
    url: str
    num_questions: int
    num_runs: int
    questions: List[Question]
    runs: List[Run]

def download_pdf(url: str) -> bytes:
    """Download PDF from URL with user agent"""
    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response = urlopen(req)
        return response.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {e}")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {e}")

def parse_questions_with_llm(text: str) -> List[Question]:
    """Use Claude to parse questions from text"""
    prompt = f"""Extract all multiple choice questions from this text. Return ONLY valid JSON with no markdown formatting.

The text may be in a two-column layout or have complex formatting. Look for:
- Question numbers (e.g., "1.", "Question 1", "1)")
- Question text (may span multiple lines)
- Answer choices labeled A, B, C, D (or similar)
- Choices may be on separate lines or inline

Format as a JSON array:
[
  {{
    "number": 1,
    "question": "question text here",
    "choices": {{
      "A": "choice A text",
      "B": "choice B text",
      "C": "choice C text",
      "D": "choice D text"
    }}
  }}
]

Text:
{text[:15000]}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        questions_data = json.loads(response_text)
        
        if not questions_data:
            raise HTTPException(status_code=400, detail="No questions found in PDF")
        
        return [Question(**q) for q in questions_data]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse questions: {e}")

def answer_question(question: Question) -> str:
    """Use Claude to answer a question"""
    choices_text = "\n".join([f"{k}. {v}" for k, v in question.choices.items()])
    
    prompt = f"""Answer this multiple choice question. Reply with ONLY the letter (A, B, C, or D).

Question: {question.question}

Choices:
{choices_text}

Reply with only the letter of the correct answer."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "The correct answer is:"}
            ]
        )
        
        answer = message.content[0].text.strip()
        # Extract just the letter
        for char in answer:
            if char.upper() in question.choices:
                return char.upper()
        
        return list(question.choices.keys())[0]
    except Exception as e:
        print(f"Error answering question: {e}")
        return list(question.choices.keys())[0]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/proxy-pdf")
async def proxy_pdf(url: str):
    """Proxy PDF to avoid CORS issues"""
    try:
        pdf_bytes = download_pdf(url)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/solve", response_model=SolveResponse)
async def solve_quiz(request: SolveRequest):
    """Download PDF, extract questions, and answer them"""
    # Download and extract
    pdf_bytes = download_pdf(request.url)
    text = extract_text_from_pdf(pdf_bytes)
    
    # Parse questions
    questions = parse_questions_with_llm(text)
    
    # Answer questions for each run
    runs = []
    for run_num in range(request.runs):
        answers = []
        for q in questions:
            model_answer = answer_question(q)
            answers.append(Answer(
                question_number=q.number,
                question_text=q.question,
                choices=q.choices,
                model_answer=model_answer
            ))
        runs.append(Run(run=run_num + 1, answers=answers))
    
    return SolveResponse(
        url=request.url,
        num_questions=len(questions),
        num_runs=request.runs,
        questions=questions,
        runs=runs
    )

@app.post("/solve-upload", response_model=SolveResponse)
async def solve_quiz_upload(file: UploadFile = File(...), runs: int = 1):
    """Upload PDF, extract questions, and answer them"""
    # Read uploaded file
    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)
    
    # Parse questions
    questions = parse_questions_with_llm(text)
    
    # Answer questions for each run
    run_list = []
    for run_num in range(runs):
        answers = []
        for q in questions:
            model_answer = answer_question(q)
            answers.append(Answer(
                question_number=q.number,
                question_text=q.question,
                choices=q.choices,
                model_answer=model_answer
            ))
        run_list.append(Run(run=run_num + 1, answers=answers))
    
    return SolveResponse(
        url=file.filename or "uploaded.pdf",
        num_questions=len(questions),
        num_runs=runs,
        questions=questions,
        runs=run_list
    )

@app.post("/answer-sheet")
async def generate_answer_sheet(request: SolveRequest):
    """Generate a PDF answer sheet with bubbles filled in"""
    # Get the answers first
    solve_response = await solve_quiz(request)
    answers = solve_response.runs[0].answers
    
    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Answer Sheet")
    
    # Draw answers in a grid
    y = height - 100
    x = 50
    
    c.setFont("Helvetica", 10)
    for answer in answers:
        if y < 50:
            c.showPage()
            y = height - 50
        
        # Question number
        c.drawString(x, y, f"{answer.question_number}.")
        
        # Draw bubbles for A, B, C, D
        bubble_x = x + 30
        for letter in ["A", "B", "C", "D"]:
            # Draw circle
            if letter == answer.model_answer:
                c.setFillColorRGB(0, 0, 0)
                c.circle(bubble_x, y + 2, 6, fill=1)
            else:
                c.setFillColorRGB(1, 1, 1)
                c.circle(bubble_x, y + 2, 6, fill=1)
                c.setStrokeColorRGB(0, 0, 0)
                c.circle(bubble_x, y + 2, 6, fill=0)
            
            # Draw letter
            c.setFillColorRGB(0, 0, 0)
            c.drawString(bubble_x - 2, y - 2, letter)
            bubble_x += 30
        
        y -= 25
    
    c.save()
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=answer_sheet.pdf"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
