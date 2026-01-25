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

function PaymentMethodSelector({ onSelect }) {
  return (
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
        Select payment method:
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        <button
          onClick={() => onSelect("cash")}
          style={{
            flex: 1,
            padding: "16px",
            border: "2px solid rgba(235, 0, 0, 0.2)",
            borderRadius: "8px",
            background: "white",
            cursor: "pointer",
            fontFamily: "inherit",
            fontSize: "1em",
            fontWeight: "600",
            color: "var(--red)",
            transition: "all 0.2s ease"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--red)";
            e.currentTarget.style.background = "rgba(235, 0, 0, 0.05)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "rgba(235, 0, 0, 0.2)";
            e.currentTarget.style.background = "white";
          }}
        >
          Cash
        </button>
        <button
          onClick={() => onSelect("finance")}
          style={{
            flex: 1,
            padding: "16px",
            border: "2px solid rgba(235, 0, 0, 0.2)",
            borderRadius: "8px",
            background: "white",
            cursor: "pointer",
            fontFamily: "inherit",
            fontSize: "1em",
            fontWeight: "600",
            color: "var(--red)",
            transition: "all 0.2s ease"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--red)";
            e.currentTarget.style.background = "rgba(235, 0, 0, 0.05)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "rgba(235, 0, 0, 0.2)";
            e.currentTarget.style.background = "white";
          }}
        >
          Finance
        </button>
      </div>
    </div>
  );
}

function FinancingForm({ onSubmit, onBack }) {
  const [formData, setFormData] = useState({
    down_payment: "",
    loan_term_months: "60",
    credit_score: "",
    max_monthly_payment: ""
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    const data = {
      down_payment: parseInt(formData.down_payment) || 0,
      loan_term_months: parseInt(formData.loan_term_months) || 60
    };

    // Credit score is required, so parse it
    const parsedCreditScore = parseInt(formData.credit_score);
    if (!isNaN(parsedCreditScore)) {
      data.credit_score = parsedCreditScore;
    }

    // Only include max_monthly_payment if it's specified
    if (formData.max_monthly_payment) {
      data.max_monthly_payment = parseInt(formData.max_monthly_payment);
    }

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} style={{
      padding: "16px",
      borderTop: "1px solid rgba(0,0,0,0.08)"
    }}>
      <div style={{
        fontSize: "0.9em",
        fontWeight: "600",
        marginBottom: "12px",
        color: "#333"
      }}>
        Financing Information:
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div>
          <label style={{ fontSize: "0.85em", color: "#666", display: "block", marginBottom: "4px" }}>
            Down Payment ($)
          </label>
          <input
            type="number"
            value={formData.down_payment}
            onChange={(e) => setFormData({ ...formData, down_payment: e.target.value })}
            placeholder="e.g., 5000"
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontFamily: "inherit",
              fontSize: "1em"
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.85em", color: "#666", display: "block", marginBottom: "4px" }}>
            Loan Term (months)
          </label>
          <select
            value={formData.loan_term_months}
            onChange={(e) => setFormData({ ...formData, loan_term_months: e.target.value })}
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontFamily: "inherit",
              fontSize: "1em"
            }}
          >
            <option value="36">36 months</option>
            <option value="48">48 months</option>
            <option value="60">60 months</option>
            <option value="72">72 months</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: "0.85em", color: "#666", display: "block", marginBottom: "4px" }}>
            Credit Score <span style={{ color: "var(--red)" }}>*</span>
          </label>
          <input
            type="number"
            value={formData.credit_score}
            onChange={(e) => setFormData({ ...formData, credit_score: e.target.value })}
            placeholder="e.g., 700"
            min="300"
            max="850"
            required
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontFamily: "inherit",
              fontSize: "1em"
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.85em", color: "#666", display: "block", marginBottom: "4px" }}>
            Max Monthly Payment ($) <span style={{ fontStyle: "italic", color: "#999" }}>(optional)</span>
          </label>
          <input
            type="number"
            value={formData.max_monthly_payment}
            onChange={(e) => setFormData({ ...formData, max_monthly_payment: e.target.value })}
            placeholder="e.g., 500"
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontFamily: "inherit",
              fontSize: "1em"
            }}
          />
          <div style={{ fontSize: "0.75em", color: "#999", marginTop: "4px" }}>
            Leave blank to use budget range instead
          </div>
        </div>

        <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
          <button
            type="button"
            onClick={onBack}
            style={{
              flex: 1,
              padding: "12px",
              border: "2px solid rgba(235, 0, 0, 0.3)",
              borderRadius: "8px",
              background: "white",
              color: "var(--red)",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "1em",
              fontWeight: "600",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--red)";
              e.currentTarget.style.background = "rgba(235, 0, 0, 0.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "rgba(235, 0, 0, 0.3)";
              e.currentTarget.style.background = "white";
            }}
          >
            Back
          </button>
          <button
            type="submit"
            style={{
              flex: 1,
              padding: "12px",
              border: "2px solid var(--red)",
              borderRadius: "8px",
              background: "var(--red)",
              color: "white",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "1em",
              fontWeight: "600",
              transition: "all 0.2s ease"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#c00000";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--red)";
            }}
          >
            Continue
          </button>
        </div>
      </div>
    </form>
  );
}

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
  const [showPaymentMethodButtons, setShowPaymentMethodButtons] = useState(false);
  const [showFinancingForm, setShowFinancingForm] = useState(false);
  const [editingCreditScore, setEditingCreditScore] = useState(false);
  const [tempCreditScore, setTempCreditScore] = useState("");
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
      features: "Features",
      payment_method: "Payment Method",
      down_payment: "Down Payment",
      loan_term_months: "Loan Term",
      credit_score: "Credit Score",
      max_monthly_payment: "Max Monthly Payment"
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

  const handleUpdateCreditScore = async (newCreditScore) => {
    const scoreNum = parseInt(newCreditScore, 10);

    // Validate credit score range
    if (isNaN(scoreNum) || scoreNum < 300 || scoreNum > 850) {
      alert("Credit score must be between 300 and 850");
      return;
    }

    const newState = { ...backendState, credit_score: scoreNum };
    setBackendState(newState);
    setEditingCreditScore(false);
    setTempCreditScore("");

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

  const handleBackFromFinancing = () => {
    // Go back to payment method selection
    setShowFinancingForm(false);
    setShowPaymentMethodButtons(true);
    setStage("payment_method");

    // Remove payment_method from state
    const newState = { ...backendState };
    delete newState.payment_method;
    setBackendState(newState);
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
      inputRef.current?.focus({ preventScroll: true });
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
      zip: stage === "zip" ? trimmed : zip,
      state: backendState  // Always send current backend state
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
      zip,
      state: backendState
    });

    // Store selected dealership and advance to payment method selection
    setDealership(selectedDealership);
    setDealerships([]);
    setStage("payment_method");
    setShowPaymentMethodButtons(true);

    if (response?.state) {
      setBackendState(response.state);
    }

    // Add bot message asking about payment method
    addBotPrompt(["How would you like to pay for your vehicle today?"]);
  };

  const handlePaymentMethodSelection = async (method) => {
    // Add user selection message
    const userMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      text: method === "cash" ? "I'll be paying in cash" : "I'll be financing"
    };
    setMessages((prev) => [...prev, userMessage]);
    setShowPaymentMethodButtons(false);

    // Update backend state with payment method
    const newState = { ...backendState, payment_method: method };
    setBackendState(newState);

    if (method === "cash") {
      // Go straight to preferences
      setStage("prefs");
      addBotPrompt(["Great! Now tell me about your vehicle preferences."]);
    } else {
      // Show financing form
      setShowFinancingForm(true);
      addBotPrompt([
        "I'll need some information to calculate your financing options.",
        "Please provide your down payment, desired loan term (in months), and credit score."
      ]);
    }
  };

  const handleFinancingSubmit = async (financingData) => {
    // Update backend state with financing info
    const newState = {
      ...backendState,
      ...financingData
    };
    setBackendState(newState);
    setShowFinancingForm(false);
    setStage("prefs");

    // Add summary message
    const summaryParts = [];
    if (financingData.down_payment) summaryParts.push(`Down payment: $${financingData.down_payment.toLocaleString()}`);
    if (financingData.loan_term_months) summaryParts.push(`${financingData.loan_term_months} month term`);
    if (financingData.credit_score) summaryParts.push(`Credit score: ${financingData.credit_score}`);
    if (financingData.max_monthly_payment) summaryParts.push(`Max monthly: $${financingData.max_monthly_payment.toLocaleString()}`);

    setMessages((prev) => [...prev, {
      id: `${Date.now()}-user`,
      role: "user",
      text: summaryParts.join(", ")
    }]);

    addBotPrompt(["Perfect! Now tell me about your vehicle preferences."]);
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
                stage === "payment_method" ? "Payment method" :
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
                    {filter.key === "credit_score" && editingCreditScore ? (
                      <>
                        <span className="filter-label">{filter.label}:</span>
                        <input
                          type="number"
                          value={tempCreditScore}
                          onChange={(e) => setTempCreditScore(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              handleUpdateCreditScore(tempCreditScore);
                            } else if (e.key === "Escape") {
                              setEditingCreditScore(false);
                              setTempCreditScore("");
                            }
                          }}
                          autoFocus
                          placeholder="300-850"
                          style={{
                            width: "60px",
                            padding: "2px 6px",
                            border: "1px solid var(--red)",
                            borderRadius: "3px",
                            fontSize: "0.9em",
                            fontFamily: "inherit"
                          }}
                        />
                        <button
                          onClick={() => handleUpdateCreditScore(tempCreditScore)}
                          style={{
                            marginLeft: "4px",
                            padding: "2px 8px",
                            border: "1px solid var(--red)",
                            borderRadius: "3px",
                            background: "var(--red)",
                            color: "white",
                            cursor: "pointer",
                            fontSize: "0.85em",
                            fontWeight: "600"
                          }}
                        >
                          ✓
                        </button>
                        <button
                          onClick={() => {
                            setEditingCreditScore(false);
                            setTempCreditScore("");
                          }}
                          style={{
                            marginLeft: "4px",
                            padding: "2px 8px",
                            border: "1px solid #666",
                            borderRadius: "3px",
                            background: "white",
                            color: "#666",
                            cursor: "pointer",
                            fontSize: "0.85em"
                          }}
                        >
                          ✕
                        </button>
                      </>
                    ) : (
                      <>
                        <span className="filter-label">{filter.label}:</span>
                        <span
                          className="filter-value"
                          style={filter.key === "credit_score" ? {
                            cursor: "pointer",
                            textDecoration: "underline",
                            textDecorationStyle: "dotted"
                          } : {}}
                          onClick={() => {
                            if (filter.key === "credit_score") {
                              setEditingCreditScore(true);
                              setTempCreditScore(filter.value.toString());
                            }
                          }}
                        >
                          {filter.displayValue}
                        </span>
                        <button
                          className="filter-remove"
                          onClick={() => handleRemoveFilter(filter.key)}
                          aria-label={`Remove ${filter.label} filter`}
                        >
                          ×
                        </button>
                      </>
                    )}
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
          ) : showPaymentMethodButtons ? (
            <PaymentMethodSelector onSelect={handlePaymentMethodSelection} />
          ) : showFinancingForm ? (
            <FinancingForm onSubmit={handleFinancingSubmit} onBack={handleBackFromFinancing} />
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
