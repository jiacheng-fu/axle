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
  const [backendState, setBackendState] = useState({});
  const [results, setResults] = useState([]);
  const [dealership, setDealership] = useState(null);
  const [dealerships, setDealerships] = useState([]);
  const chatRailRef = useRef(null);
  const inputRef = useRef(null);

  const canShowResults = useMemo(() => zip && prefCount > 0, [zip, prefCount]);

  const formatLabel = (key) => {
    const labelMap = {
      zip: "Zip Code",
      brand: "Brand",
      model: "Model",
      min_year: "Min Year",
      max_year: "Max Year",
      min_price: "Min Price",
      max_price: "Max Price",
      max_mileage: "Max Mileage",
      exterior_color: "Exterior Color",
      body_type: "Body Type",
      seating_capacity: "Seating",
      horsepower: "Horsepower",
      interior_color: "Interior Color",
      drivetrain: "Drivetrain",
      features: "Features"
    };
    return labelMap[key] || key;
  };

  const formatValue = (value) => {
    if (Array.isArray(value)) {
      return value.join(", ");
    }
    if (typeof value === "number") {
      return value.toLocaleString();
    }
    return value;
  };

  const summaryFilters = useMemo(() => {
    const entries = Object.entries(backendState);
    if (!entries.length) return [];

    const filtered = entries
      .filter(([key, value]) => {
        // Filter out dealership object and empty values
        if (key === "dealership") return false;
        if (value === null || value === undefined || value === "") return false;
        if (Array.isArray(value) && value.length === 0) return false;
        return true;
      })
      .map(([key, value]) => ({
        key,
        label: formatLabel(key),
        value: formatValue(value),
        displayValue: formatValue(value)
      }));

    console.log("[summaryFilters] backendState:", backendState);
    console.log("[summaryFilters] filtered:", filtered);

    return filtered;
  }, [backendState]);

  const handleRemoveFilter = async (filterKey) => {
    const newState = { ...backendState };
    delete newState[filterKey];
    setBackendState(newState);

    // Re-rank with updated state if we're already showing results
    if (showPanels && stage === "done") {
      const response = await sendUserMessage({
        text: "show_results",
        stage: "done",
        zip,
        state: newState  // Pass updated state to backend
      });

      if (response?.results) {
        setResults(response.results);
      }
      if (response?.state) {
        setBackendState(response.state);
      }
    }
  };

  useEffect(() => {
    if (!showPanels) return;

    const handleMouseMove = (event) => {
      // Open chat when mouse is near left edge
      if (event.clientX <= 28 && !chatOpen) {
        setChatOpen(true);
      }
      // Close chat when mouse moves away from chat area
      else if (chatOpen && chatRailRef.current) {
        const chatRect = chatRailRef.current.getBoundingClientRect();
        // Check if mouse is outside the chat area (with a small buffer)
        if (event.clientX > chatRect.right + 20) {
          setChatOpen(false);
        }
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

    // Check if user is giving an affirmative response to see results
    const affirmativePattern = /^(yes|yeah|yep|sure|ok|okay|show me|let's see|please|go ahead|sounds good|perfect|great|absolutely)\b/i;
    const isAffirmative = affirmativePattern.test(trimmed);

    const payload = {
      text: trimmed,
      stage,
      zip: stage === "zip" ? trimmed : zip
    };

    const response = await sendUserMessage(payload);

    // Handle zip validation
    if (stage === "zip") {
      if (response?.error) {
        // Invalid zip - stay on zip stage, show error
        if (response?.bot_response) {
          addBotPrompt([response.bot_response]);
        }
        return;
      }

      // Valid zip - show dealership selection
      setZip(trimmed);
      setStage("select_dealership");
      setBackendState({ zip: trimmed, features: [] });
      setResults([]);

      // Store dealership options
      if (response?.dealerships) {
        setDealerships(response.dealerships);
      }
    } else {
      setPrefCount((count) => count + 1);
    }

    if (response?.state) {
      setBackendState(response.state);
    }
    if (response?.bot_response) {
      addBotPrompt([response.bot_response]);
    }

    // Auto-transition to results if user gave affirmative response and we can show results
    if (isAffirmative && canShowResults && stage === "prefs") {
      // Small delay to let the bot response render first
      setTimeout(() => {
        handleShowResults();
      }, 800);
    }
  };

  const handleSelectDealership = async (selectedDealership) => {
    // Add user selection message
    const userMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      text: `I'll use ${selectedDealership.name}`
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send dealership selection to backend
    const response = await sendUserMessage({
      text: selectedDealership.name,
      stage: "select_dealership",
      zip
    });

    // Store selected dealership and advance to prefs
    setDealership(selectedDealership);
    setDealerships([]);
    setStage("prefs");

    if (response?.state) {
      setBackendState(response.state);
    }
    if (response?.bot_response) {
      addBotPrompt([response.bot_response]);
    }
  };

  const handleShowResults = async () => {
    if (!canShowResults) return;

    setStage("done");
    setShowPanels(true);
    setChatOpen(false);

    const response = await sendUserMessage({
      text: "show_results",
      stage: "done",
      zip,
      state: backendState  // Pass current state to ensure sync
    });
    if (response?.state) {
      setBackendState(response.state);
    }
    if (response?.results) {
      setResults(response.results);
    }
    if (response?.bot_response) {
      addBotPrompt([response.bot_response]);
    }
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
              <span>{
                stage === "zip" ? "Collecting zip" :
                stage === "select_dealership" ? "Selecting dealership" :
                stage === "prefs" ? "Collecting preferences" :
                "Ready"
              }</span>
            </div>
          </div>
          <div className="summary-strip">
            <span className="summary-title">Captured parameters</span>
            {dealership && (
              <div className="summary-dealership" style={{
                padding: "8px 12px",
                background: "rgba(235, 0, 0, 0.08)",
                borderRadius: "6px",
                marginBottom: "8px",
                fontSize: "0.9em"
              }}>
                <strong style={{ color: "var(--red)" }}>📍 {dealership.name}</strong>
                <div style={{ fontSize: "0.85em", color: "#666", marginTop: "2px" }}>
                  {dealership.address}
                </div>
              </div>
            )}
            {summaryFilters.length ? (
              <div className="summary-filters">
                {summaryFilters.map((filter) => (
                  <div key={filter.key} className="filter-badge">
                    <span className="filter-label">{filter.label}:</span>
                    <span className="filter-value">{filter.displayValue}</span>
                    <button
                      className="filter-remove"
                      onClick={() => handleRemoveFilter(filter.key)}
                      aria-label={`Remove ${filter.label} filter`}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <span className="summary-empty">No parameters captured yet.</span>
            )}
          </div>

          <MessageList messages={messages} />

          {dealerships.length > 0 ? (
            <div style={{
              padding: "16px",
              borderTop: "1px solid rgba(0,0,0,0.08)"
            }}>
              <div style={{
                fontSize: "0.9em",
                fontWeight: "600",
                marginBottom: "12px",
                color: "#333"
              }}>
                Select a dealership:
              </div>
              {dealerships.map((dealer, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectDealership(dealer)}
                  style={{
                    width: "100%",
                    padding: "16px",
                    marginBottom: "8px",
                    border: "2px solid rgba(235, 0, 0, 0.2)",
                    borderRadius: "8px",
                    background: "white",
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.2s ease",
                    fontFamily: "inherit"
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--red)";
                    e.currentTarget.style.background = "rgba(235, 0, 0, 0.02)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "rgba(235, 0, 0, 0.2)";
                    e.currentTarget.style.background = "white";
                  }}
                >
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "start"
                  }}>
                    <div>
                      <div style={{
                        fontWeight: "600",
                        fontSize: "1em",
                        color: "var(--red)",
                        marginBottom: "4px"
                      }}>
                        {dealer.name}
                      </div>
                      <div style={{
                        fontSize: "0.85em",
                        color: "#666",
                        marginBottom: "4px"
                      }}>
                        {dealer.address}
                      </div>
                      <div style={{
                        fontSize: "0.85em",
                        color: "#888"
                      }}>
                        {dealer.phone} • {dealer.hours}
                      </div>
                    </div>
                    <div style={{
                      fontSize: "0.85em",
                      color: "var(--red)",
                      fontWeight: "600",
                      whiteSpace: "nowrap",
                      marginLeft: "12px"
                    }}>
                      {dealer.distance}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <Composer
              value={input}
              onChange={setInput}
              onSend={handleSend}
              onShowResults={handleShowResults}
              canShowResults={canShowResults}
              stage={stage}
              inputRef={inputRef}
            />
          )}
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
            <ResultsShell results={results} />
            <ComparisonShell />
          </section>
        )}
      </main>
    </div>
  );
}
