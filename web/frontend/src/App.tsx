import { useState } from "react";
import "./App.css";

interface Question {
  number: number;
  question: string;
  choices: Record<string, string>;
}

interface Answer {
  question_number: number;
  question_text: string;
  choices: Record<string, string>;
  model_answer: string;
}

interface Run {
  run: number;
  answers: Answer[];
}

interface SolveResult {
  url: string;
  num_questions: number;
  num_runs: number;
  questions: Question[];
  runs: Run[];
}

type ViewMode = "detailed" | "compact" | "grid";

function App() {
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SolveResult | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("detailed");
  const [showPdf, setShowPdf] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      setUrl("");
      setError(null);
    } else if (selectedFile) {
      setError("Please select a PDF file");
    }
  };

  const handleSolve = async () => {
    if (!url.trim() && !file) {
      setError("Please enter a PDF URL or upload a file");
      return;
    }

    setLoading(true);
    setLoadingStatus("Processing...");
    setError(null);
    setResult(null);

    try {
      let response;
      
      if (file) {
        // Upload file
        const formData = new FormData();
        formData.append("file", file);
        formData.append("runs", "1");
        
        response = await fetch("http://localhost:8001/solve-upload", {
          method: "POST",
          body: formData,
        });
        
        // Set PDF URL for viewing
        setPdfUrl(URL.createObjectURL(file));
      } else {
        // Use URL
        setPdfUrl(`http://localhost:8001/proxy-pdf?url=${encodeURIComponent(url.trim())}`);
        
        response = await fetch("http://localhost:8001/solve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: url.trim(), runs: 1 }),
        });
      }

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to solve quiz");
      }

      const data = await response.json();
      setResult(data);
      setLoadingStatus("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setLoadingStatus("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Do My Homework</h1>
      </header>

      <main className="main">
        <div className="input-section">
          <div className="input-group">
            <input
              type="url"
              placeholder="Paste PDF URL here..."
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setFile(null);
              }}
              disabled={loading || !!file}
              onKeyDown={(e) => e.key === "Enter" && handleSolve()}
            />
            <div className="divider">OR</div>
            <label className="file-upload">
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                disabled={loading || !!url}
              />
              <span>{file ? file.name : "Choose PDF file..."}</span>
            </label>
          </div>
          <button onClick={handleSolve} disabled={loading}>
            {loading ? "Solving..." : "Solve Quiz"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>{loadingStatus}</p>
          </div>
        )}

        {pdfUrl && (
          <div className="pdf-toggle-bar">
            <button
              className="pdf-toggle-btn"
              onClick={() => setShowPdf(!showPdf)}
            >
              {showPdf ? "Hide PDF" : "Show PDF"}
            </button>
          </div>
        )}

        {showPdf && pdfUrl && (
          <div className="pdf-viewer-standalone">
            <iframe src={pdfUrl} title="Quiz PDF" />
          </div>
        )}

        {result && (
          <div className="results-area">
            <div className="results">
              <div className="summary">
                <span className="count">{result.num_questions} questions solved</span>
                <div className="view-controls">
                  <button
                    className={`view-btn ${viewMode === "detailed" ? "active" : ""}`}
                    onClick={() => setViewMode("detailed")}
                  >
                    Detailed
                  </button>
                  <button
                    className={`view-btn ${viewMode === "compact" ? "active" : ""}`}
                    onClick={() => setViewMode("compact")}
                  >
                    Compact
                  </button>
                  <button
                    className={`view-btn ${viewMode === "grid" ? "active" : ""}`}
                    onClick={() => setViewMode("grid")}
                  >
                    Grid
                  </button>
                </div>
              </div>

              {viewMode === "compact" && (
                <div className="compact-view">
                  {result.runs[0].answers.map((a, idx) => (
                    <div key={idx} className="compact-answer">
                      <span className="compact-num">{a.question_number}</span>
                      <span className="compact-letter">{a.model_answer}</span>
                    </div>
                  ))}
                </div>
              )}

              {viewMode === "grid" && (
                <div className="grid-view">
                  {result.questions.map((q, idx) => {
                    const answer = result.runs[0]?.answers[idx]?.model_answer;
                    return (
                      <div key={idx} className="grid-card">
                        <div className="grid-header">
                          <span className="grid-number">{q.number}</span>
                        </div>
                        <p className="grid-question">{q.question}</p>
                        <div className="grid-choices">
                          {Object.entries(q.choices).map(([letter, text]) => (
                            <div
                              key={letter}
                              className={`grid-choice ${answer === letter ? "selected" : ""}`}
                            >
                              <span className="grid-choice-letter">{letter}</span>
                              <span className="grid-choice-text">{text}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {viewMode === "detailed" && (
                <div className="questions-list">
                  {result.questions.map((q, idx) => {
                    const answer = result.runs[0]?.answers[idx]?.model_answer;
                    return (
                      <div key={idx} className="question-card">
                        <div className="question-header">
                          <span className="question-number">{q.number}</span>
                          <p className="question-text">{q.question}</p>
                        </div>
                        <div className="choices">
                          {Object.entries(q.choices).map(([letter, text]) => (
                            <div
                              key={letter}
                              className={`choice ${answer === letter ? "selected" : ""}`}
                            >
                              <span className="choice-letter">{letter}</span>
                              <span className="choice-text">{text}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
