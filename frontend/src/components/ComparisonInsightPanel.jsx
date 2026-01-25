import React, { useState, useEffect, useRef } from "react";

// Simple markdown renderer component
function SimpleMarkdown({ children }) {
  if (!children) return null;

  const renderMarkdown = (text) => {
    const lines = text.split('\n');
    const elements = [];
    let currentList = null;
    let listItems = [];

    const flushList = () => {
      if (currentList && listItems.length > 0) {
        elements.push(
          <ul key={`list-${elements.length}`} style={{ margin: '12px 0', paddingLeft: '24px', lineHeight: '1.7' }}>
            {listItems.map((item, i) => (
              <li key={i} style={{ margin: '6px 0' }} dangerouslySetInnerHTML={{ __html: processInlineFormatting(item) }} />
            ))}
          </ul>
        );
        listItems = [];
        currentList = null;
      }
    };

    const processInlineFormatting = (text) => {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 0.9em;">$1</code>');
    };

    lines.forEach((line, index) => {
      line = line.trim();

      if (!line) {
        flushList();
        return;
      }

      // Headers
      if (line.startsWith('### ')) {
        flushList();
        elements.push(
          <h3 key={`h3-${index}`} style={{ fontSize: '1.25em', marginTop: '20px', marginBottom: '12px', color: 'var(--red)', fontFamily: '"Oswald", sans-serif' }}>
            {line.substring(4)}
          </h3>
        );
      } else if (line.startsWith('## ')) {
        flushList();
        elements.push(
          <h2 key={`h2-${index}`} style={{ fontSize: '1.5em', marginTop: '20px', marginBottom: '12px', borderBottom: '1px solid #e0e0e0', paddingBottom: '6px', fontFamily: '"Oswald", sans-serif' }}>
            {line.substring(3)}
          </h2>
        );
      } else if (line.startsWith('# ')) {
        flushList();
        elements.push(
          <h1 key={`h1-${index}`} style={{ fontSize: '1.8em', marginTop: '20px', marginBottom: '12px', borderBottom: '2px solid #e0e0e0', paddingBottom: '8px', fontFamily: '"Oswald", sans-serif' }}>
            {line.substring(2)}
          </h1>
        );
      }
      // List items
      else if (line.startsWith('- ') || line.startsWith('* ')) {
        listItems.push(line.substring(2));
        currentList = 'ul';
      }
      // Regular paragraph
      else {
        flushList();
        elements.push(
          <p key={`p-${index}`} style={{ margin: '12px 0', lineHeight: '1.7' }} dangerouslySetInnerHTML={{ __html: processInlineFormatting(line) }} />
        );
      }
    });

    flushList();
    return elements;
  };

  return <div className="markdown-content">{renderMarkdown(children)}</div>;
}

export default function ComparisonInsightPanel({ cars, isOpen, onClose }) {
  const [aiInsight, setAiInsight] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const chatEndRef = useRef(null);
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const [car1, car2] = cars;

  // Fetch AI insight when panel opens with 2 cars
  useEffect(() => {
    if (isOpen && car1 && car2 && !aiInsight && !loadingInsight) {
      fetchAiInsight();
    }
  }, [isOpen, car1, car2]);

  // Scroll chat to bottom when messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  const fetchAiInsight = async () => {
    setLoadingInsight(true);
    try {
      const response = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          car1: car1,
          car2: car2
        })
      });

      if (!response.ok) throw new Error("Failed to fetch AI insight");

      const data = await response.json();
      setAiInsight(data.insight);
    } catch (error) {
      console.error("Failed to fetch AI insight:", error);
      setAiInsight("Unable to generate AI insight at this time. Please try again later.");
    } finally {
      setLoadingInsight(false);
    }
  };

  const handleSendChatMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = { role: "user", text: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setLoadingChat(true);

    try {
      const response = await fetch(`${API_BASE}/compare-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          car1: car1,
          car2: car2,
          question: chatInput,
          chat_history: chatMessages
        })
      });

      if (!response.ok) throw new Error("Failed to get chat response");

      const data = await response.json();
      const botMessage = { role: "bot", text: data.answer };
      setChatMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Failed to send chat message:", error);
      const errorMessage = { role: "bot", text: "Sorry, I couldn't process that question. Please try again." };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoadingChat(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendChatMessage();
    }
  };

  if (!car1 || !car2) return null;

  return (
    <div style={{
      position: "fixed",
      right: isOpen ? 0 : "-50%",
      top: 0,
      width: "45%",
      height: "100vh",
      background: "white",
      transition: "right 0.3s ease-in-out",
      zIndex: 1001,
      display: "flex",
      flexDirection: "column",
      boxShadow: "-2px 0 10px rgba(0, 0, 0, 0.1)"
    }}>
      {/* Header */}
      <div style={{
        padding: "20px",
        borderBottom: "1px solid #ddd",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: "var(--red)",
        color: "white"
      }}>
        <h2 style={{ margin: 0, fontSize: "1.4em" }}>AI Insights</h2>
        <button
          onClick={onClose}
          style={{
            background: "transparent",
            border: "2px solid white",
            color: "white",
            fontSize: "1.2em",
            cursor: "pointer",
            borderRadius: "4px",
            padding: "4px 12px",
            fontWeight: "bold"
          }}
        >
          ×
        </button>
      </div>

      {/* AI Insight Section */}
      <div style={{
        flex: "0 0 auto",
        maxHeight: "45vh",
        overflowY: "auto",
        padding: "32px",
        borderBottom: "2px solid #ddd"
      }}>
        <h3 style={{
          marginTop: 0,
          marginBottom: "20px",
          fontSize: "1.2em",
          color: "#333"
        }}>
          Comparison Analysis
        </h3>
        {loadingInsight ? (
          <div style={{
            textAlign: "center",
            padding: "40px",
            color: "#666",
            fontSize: "1em"
          }}>
            Loading AI insight...
          </div>
        ) : (
          <div style={{
            fontSize: "0.95em",
            lineHeight: "1.7",
            color: "#333"
          }}>
            <SimpleMarkdown>{aiInsight || "No insight available"}</SimpleMarkdown>
          </div>
        )}
      </div>

      {/* Chat Section */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        background: "#f9f9f9",
        minHeight: 0
      }}>
        <div style={{
          padding: "20px 32px 16px 32px",
          borderBottom: "1px solid #ddd",
          background: "white"
        }}>
          <h3 style={{
            margin: 0,
            fontSize: "1.1em",
            color: "#333"
          }}>
            Ask Questions
          </h3>
          <p style={{
            margin: "8px 0 0 0",
            fontSize: "0.85em",
            color: "#666"
          }}>
            Ask anything about these two vehicles
          </p>
        </div>

        {/* Chat Messages */}
        <div style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 32px",
          minHeight: 0
        }}>
          {chatMessages.length === 0 ? (
            <div style={{
              textAlign: "center",
              padding: "40px 20px",
              color: "#999",
              fontSize: "0.9em"
            }}>
              No messages yet. Ask a question about these cars!
            </div>
          ) : (
            chatMessages.map((msg, index) => (
              <div
                key={index}
                style={{
                  marginBottom: "16px",
                  padding: "14px 18px",
                  borderRadius: "8px",
                  background: msg.role === "user" ? "#e3f2fd" : "white",
                  border: msg.role === "bot" ? "1px solid #ddd" : "none"
                }}
              >
                <div style={{
                  fontWeight: "bold",
                  marginBottom: "6px",
                  fontSize: "0.85em",
                  color: msg.role === "user" ? "#1976d2" : "var(--red)"
                }}>
                  {msg.role === "user" ? "You" : "AI"}
                </div>
                <div style={{
                  fontSize: "0.95em",
                  lineHeight: "1.6",
                  color: "#333"
                }}>
                  {msg.text}
                </div>
              </div>
            ))
          )}
          {loadingChat && (
            <div style={{
              marginBottom: "16px",
              padding: "14px 18px",
              borderRadius: "8px",
              background: "white",
              border: "1px solid #ddd",
              color: "#666",
              fontSize: "0.95em"
            }}>
              Thinking...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Chat Input */}
        <div style={{
          padding: "20px 32px",
          borderTop: "1px solid #ddd",
          background: "white"
        }}>
          <div style={{
            display: "flex",
            gap: "12px"
          }}>
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "0.95em",
                resize: "none",
                fontFamily: "inherit",
                minHeight: "44px",
                maxHeight: "120px"
              }}
              rows={2}
            />
            <button
              onClick={handleSendChatMessage}
              disabled={!chatInput.trim() || loadingChat}
              style={{
                padding: "12px 24px",
                background: chatInput.trim() && !loadingChat ? "var(--red)" : "#ccc",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: chatInput.trim() && !loadingChat ? "pointer" : "not-allowed",
                fontSize: "0.95em",
                fontWeight: "600",
                whiteSpace: "nowrap"
              }}
            >
              Send
            </button>
          </div>
          <p style={{
            margin: "8px 0 0 0",
            fontSize: "0.75em",
            color: "#999"
          }}>
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
