import React, { useEffect, useMemo, useRef, useState } from "react";
import BrandHeader from "./components/BrandHeader.jsx";
import MessageList from "./components/MessageList.jsx";
import Composer from "./components/Composer.jsx";
import ResultsShell from "./components/ResultsShell.jsx";
import ComparisonShell from "./components/ComparisonShell.jsx";
import { sendUserMessage } from "./api/client.js";

const initialMessages = [
  {
    id: "intro-1",
    role: "bot",
    text: "Welcome to Redline Scout. I can help you narrow down the right used car."
  },
  {
    id: "intro-2",
    role: "bot",
    text: "First, what zip code should I use for your search?"
  }
];

export default function App() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [stage, setStage] = useState("zip");
  const [zip, setZip] = useState("");
  const [prefCount, setPrefCount] = useState(0);
  const [showPanels, setShowPanels] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const chatRailRef = useRef(null);
  const inputRef = useRef(null);

  const canShowResults = useMemo(() => zip && prefCount > 0, [zip, prefCount]);

  useEffect(() => {
    if (!showPanels || chatOpen) return;

    const handleMouseMove = (event) => {
      if (event.clientX <= 28) {
        setChatOpen(true);
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [showPanels, chatOpen]);

  useEffect(() => {
    if (!showPanels || !chatOpen) return;
    const handleOutsideClick = (event) => {
      if (!chatRailRef.current) return;
      if (!chatRailRef.current.contains(event.target)) {
        setChatOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [showPanels, chatOpen]);

  useEffect(() => {
    if (!showPanels || !chatOpen) return;
    const timer = setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => clearTimeout(timer);
  }, [showPanels, chatOpen]);

  const addBotPrompt = (textArray) => {
    setMessages((prev) => [
      ...prev,
      ...textArray.map((text) => ({
        id: `${Date.now()}-${Math.random()}`,
        role: "bot",
        text
      }))
    ]);
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      text: trimmed
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    const payload = {
      text: trimmed,
      stage,
      zip: stage === "zip" ? trimmed : zip
    };

    if (stage === "zip") {
      setZip(trimmed);
      setStage("prefs");
      addBotPrompt([
        `Got it. I will search around ${trimmed}.`,
        "Now tell me the features, budget, or brands you want.",
        "Is there anything else you'd like to add?"
      ]);
    } else {
      setPrefCount((count) => count + 1);
      addBotPrompt([
        `Noted: ${trimmed}.`,
        "Is there anything else you'd like to add?"
      ]);
    }

    await sendUserMessage(payload);
  };

  const handleShowResults = async () => {
    if (!canShowResults) return;

    setStage("done");
    setShowPanels(true);
    setChatOpen(false);
    addBotPrompt([
      "Perfect. I'll line up the best matches and get them ready for you.",
      "Results will appear below once the backend is wired up."
    ]);

    await sendUserMessage({
      text: "show_results",
      stage: "done",
      zip
    });
  };

  return (
    <div className="page">
      <div className="bg-orb orb-1" aria-hidden="true" />
      <div className="bg-orb orb-2" aria-hidden="true" />
      <div className="bg-grid" aria-hidden="true" />

      <BrandHeader />

      <main className="content">
        <div
          ref={chatRailRef}
          className={`chat-rail ${showPanels ? "chat-rail-active" : ""} ${
            showPanels && !chatOpen ? "chat-rail-collapsed" : ""
          }`}
        >
          <section className="chat-card">
          <div className="chat-header">
            <div>
              <h2>Chat with Scout</h2>
              <p>Keep adding details until you are ready to see results.</p>
            </div>
            <div className="chat-status">
              <span className={`status-dot status-${stage}`} />
              <span>{stage === "zip" ? "Collecting zip" : stage === "prefs" ? "Collecting preferences" : "Ready"}</span>
            </div>
          </div>

          <MessageList messages={messages} />

          <Composer
            value={input}
            onChange={setInput}
            onSend={handleSend}
            onShowResults={handleShowResults}
            canShowResults={canShowResults}
            stage={stage}
            inputRef={inputRef}
          />
          </section>
          {showPanels && (
            <button
              type="button"
              className={`chat-toggle ${chatOpen ? "chat-toggle-open" : ""}`}
              aria-label={chatOpen ? "Hide chat" : "Open chat"}
              onClick={() => setChatOpen((open) => !open)}
            >
              <span className="chat-toggle-icon">...</span>
            </button>
          )}
        </div>
        {showPanels && (
          <section className="results-stage">
            <ResultsShell />
            <ComparisonShell />
          </section>
        )}
      </main>
    </div>
  );
}
