import { useState, useRef } from "react";
import "./App.css";

const API_BASE = "https://rag-qa-system-9qtm.onrender.com";

function App() {
  const [files, setFiles] = useState([]); // {name, chunks}
  const [selectedSource, setSelectedSource] = useState("all");
  const [messages, setMessages] = useState([]); // {role: 'user'|'assistant', text, source}
  const [question, setQuestion] = useState("");
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF file.");
      return;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      const data = await res.json();
      setFiles((prev) => [...prev, { name: data.filename, chunks: data.chunks_created }]);
    } catch (err) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    const userMessage = { role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);
    setAsking(true);
    setQuestion("");

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage.text,
          source: selectedSource === "all" ? null : selectedSource,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Request failed");
      }
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}`, sources: [] },
      ]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo-badge">
          <i className="ti ti-file-search" aria-hidden="true"></i>
        </div>
        <h1>Document Q&amp;A</h1>
        <p className="subtitle">Upload a PDF and ask anything about it</p>
      </header>

      <div className="card">
        <h2>
          <i className="ti ti-files" aria-hidden="true"></i>
          Documents
        </h2>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <i className="ti ti-cloud-upload dropzone-icon" aria-hidden="true"></i>
          <div className="dropzone-text">
            {uploading ? "Uploading..." : "Drag and drop a PDF here"}
          </div>
          <div className="dropzone-subtext">or click to browse</div>
        </div>
        <input
          type="file"
          accept=".pdf"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={(e) => handleFileUpload(e.target.files[0])}
        />
        <div className="file-list">
          {files.length === 0 && (
            <div className="empty-hint">No documents yet</div>
          )}
          {files.map((f) => (
            <div key={f.name} className="file-item">
              <div className="file-info">
                <i className="ti ti-file-type-pdf file-icon" aria-hidden="true"></i>
                <span>{f.name}</span>
              </div>
              <span className="chunk-badge">{f.chunks} chunks</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="source-row">
          <label>
            <i className="ti ti-filter" aria-hidden="true"></i>
            Ask about
          </label>
          <select value={selectedSource} onChange={(e) => setSelectedSource(e.target.value)}>
            <option value="all">All documents</option>
            {files.map((f) => (
              <option key={f.name} value={f.name}>
                {f.name}
              </option>
            ))}
          </select>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-chat">
              <i className="ti ti-message-circle-2" aria-hidden="true"></i>
              <p>Ask a question to get started</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <div className="bubble">
                {m.text}
                {m.sources && m.sources.length > 0 && (
                  <div className="source-tag">
                    <i className="ti ti-file-type-pdf" aria-hidden="true"></i>
                    {m.sources.join(", ")}
                  </div>
                )}
              </div>
            </div>
          ))}
          {asking && (
            <div className="message assistant">
              <div className="bubble typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
        </div>

        <div className="input-row">
          <input
            type="text"
            placeholder="Ask a question about your documents"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          />
          <button onClick={handleAsk} disabled={asking}>
            <i className="ti ti-send-2" aria-hidden="true"></i>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;