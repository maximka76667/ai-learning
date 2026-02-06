import { useState, useRef } from "react";
import "./App.css";

function App() {
  const [status, setStatus] = useState("Enter your feeling below");
  const [encouragement, setEncouragement] = useState("");
  const [userInput, setUserInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  // Store reference to EventSource so we can close it if needed
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleSubmit = () => {
    if (!userInput.trim()) return;
    if (isProcessing) return; // Prevent double submission

    // Close any previous EventSource connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Clear previous results
    setEncouragement("");
    setStatus("Starting...");
    setIsProcessing(true);

    const eventSource = new EventSource(
      `http://127.0.0.1:8000/stream?user_input=${encodeURIComponent(userInput)}`
    );
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      // Always set the message from backend
      if (data.message) {
        setStatus(data.message);
      }

      // Handle encouragement data
      if (data.status === "complete" && data.data?.output) {
        setEncouragement(data.data.output);
      }

      // Close connection when complete or error
      if (data.status === "complete" || data.status === "error") {
        eventSource.close();
        eventSourceRef.current = null;
        setIsProcessing(false);
      }
    };

    eventSource.onerror = () => {
      setStatus("❌ Connection error");
      eventSource.close();
      eventSourceRef.current = null;
      setIsProcessing(false);
    };
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isProcessing) {
      handleSubmit();
    }
  };

  return (
    <div className="container">
      <h1>Feeling Interpreter</h1>

      <div className="status-area">
        <p className="status">{status}</p>
        {encouragement && (
          <div className="encouragement">
            <strong>{encouragement}</strong>
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="How are you feeling?"
          disabled={isProcessing}
        />
        <button
          onClick={handleSubmit}
          disabled={isProcessing || !userInput.trim()}
        >
          {isProcessing ? "Processing..." : "Submit"}
        </button>
      </div>
    </div>
  );
}

export default App;
