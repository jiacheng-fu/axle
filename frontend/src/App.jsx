import React, { useEffect, useMemo, useRef, useState } from "react";
import BrandHeader from "./components/BrandHeader.jsx";
import LocationPicker from "./components/LocationPicker.jsx";
import MessageList from "./components/MessageList.jsx";
import Composer from "./components/Composer.jsx";
import ResultsShell from "./components/ResultsShell.jsx";
import ComparisonPanel from "./components/ComparisonPanel.jsx";
import ComparisonInsightPanel from "./components/ComparisonInsightPanel.jsx";
import TopBar from "./components/TopBar.jsx";
import LandingPage from "./components/LandingPage.jsx";
import { useAccount } from "./account/AccountContext.jsx";
import { sendUserMessage } from "./api/client.js";

const dealerKey = (d) => d.id || `${d.name}__${d.address}`;

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [zip, setZip] = useState("");
  const [radius, setRadius] = useState(50);
  const [showPanels, setShowPanels] = useState(false);
  const [backendState, setBackendState] = useState({});
  const [results, setResults] = useState([]);
  const [selectedDealerIds, setSelectedDealerIds] = useState([]);
  const [selectedDealerships, setSelectedDealerships] = useState([]);
  const [editingCreditScore, setEditingCreditScore] = useState(false);
  const [tempCreditScore, setTempCreditScore] = useState("");
  const [creditError, setCreditError] = useState("");
  const [selectedCars, setSelectedCars] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  const [showInsightPanel, setShowInsightPanel] = useState(false);
  const [compareNotice, setCompareNotice] = useState("");
  const [view, setView] = useState("browse"); // "browse" | "saved"
  const [guestEntered, setGuestEntered] = useState(false);
  const account = useAccount();
  const inputRef = useRef(null);

  // Landing -> login -> tool. With Supabase configured, login is the gate;
  // without it, the landing button enters the tool as a guest so it still runs.
  const entered = account.configured ? !!account.user : guestEntered;
  const handleEnter = () => {
    if (account.configured) account.signInWithGoogle();
    else setGuestEntered(true);
  };

  const handleToggleSave = async (car) => {
    const result = await account.toggleSave(car);
    if (result === "signin") account.signInWithGoogle();
  };

  const formatLabel = (key) => {
    const labelMap = {
      zip: "Zip Code", brand: "Brand", model: "Model", min_year: "Min Year",
      max_year: "Max Year", min_price: "Min Price", max_price: "Max Price",
      max_mileage: "Max Mileage", exterior_color: "Exterior Color", body_type: "Body Type",
      seating_capacity: "Seating", horsepower: "Horsepower", interior_color: "Interior Color",
      drivetrain: "Drivetrain", features: "Features", payment_method: "Payment Method",
      down_payment: "Down Payment", loan_term_months: "Loan Term", credit_score: "Credit Score",
      max_monthly_payment: "Max Monthly Payment"
    };
    return labelMap[key] || key;
  };

  const formatValue = (value) => {
    if (Array.isArray(value)) return value.join(", ");
    if (typeof value === "number") return value.toLocaleString();
    return value;
  };

  const summaryFilters = useMemo(() => {
    return Object.entries(backendState)
      .filter(([key, value]) => {
        if (key === "dealership" || key === "zip") return false;
        if (value === null || value === undefined || value === "") return false;
        if (Array.isArray(value) && value.length === 0) return false;
        return true;
      })
      .map(([key, value]) => ({
        key, label: formatLabel(key), value: formatValue(value), displayValue: formatValue(value)
      }));
  }, [backendState]);

  // True once a real ranking preference exists — gates "match %" vs plain inventory.
  const hasPreferences = useMemo(() => summaryFilters.length > 0, [summaryFilters]);

  const addBotPrompt = (textArray) => {
    setMessages((prev) => [
      ...prev,
      ...textArray.map((text) => ({ id: `${Date.now()}-${Math.random()}`, role: "bot", text }))
    ]);
  };

  // Re-rank against the backend whenever captured state changes post-browse.
  const rerank = async (newState) => {
    const response = await sendUserMessage({
      text: "show_results", stage: "done", zip, radius,
      dealer_ids: selectedDealerIds, state: newState
    });
    if (response?.results) setResults(response.results);
    if (response?.state) setBackendState(response.state);
  };

  const handleRemoveFilter = async (filterKey) => {
    const newState = { ...backendState };
    delete newState[filterKey];
    setBackendState(newState);
    if (showPanels) await rerank(newState);
  };

  const handleUpdateCreditScore = async (newCreditScore) => {
    const scoreNum = parseInt(newCreditScore, 10);
    if (isNaN(scoreNum) || scoreNum < 300 || scoreNum > 850) {
      setCreditError("Credit score must be between 300 and 850.");
      return;
    }
    const newState = { ...backendState, credit_score: scoreNum };
    setBackendState(newState);
    setEditingCreditScore(false);
    setTempCreditScore("");
    setCreditError("");
    if (showPanels) await rerank(newState);
  };

  const handleToggleCompare = (car) => {
    setSelectedCars((prev) => {
      const isAlreadySelected = prev.some((c) => c.id === car.id);
      if (isAlreadySelected) {
        const newSelection = prev.filter((c) => c.id !== car.id);
        if (newSelection.length < 2) setShowComparison(false);
        setCompareNotice("");
        return newSelection;
      }
      if (prev.length >= 2) {
        setCompareNotice("You can compare 2 cars at a time — deselect one first.");
        return prev;
      }
      const newSelection = [...prev, car];
      setCompareNotice("");
      if (newSelection.length === 2) {
        setShowComparison(true);
      }
      return newSelection;
    });
  };

  // Location step done -> browse-first: pull inventory from the selected dealers.
  const handleProceed = async ({ zip: z, radius: r, dealerIds, dealers }) => {
    setZip(z);
    setRadius(r);
    setSelectedDealerIds(dealerIds);
    setSelectedDealerships(dealers);
    const base = { zip: z, features: [] };
    setBackendState(base);
    setMessages([{
      id: "greet",
      role: "bot",
      text: `Showing inventory from ${dealers.length} dealership${dealers.length === 1 ? "" : "s"} within ${r} mi. Tell me what you're after — budget, body type, features, even financing — and I'll rank these for you.`
    }]);
    setShowPanels(true);

    const response = await sendUserMessage({
      text: "show_results", stage: "done", zip: z, radius: r, dealer_ids: dealerIds, state: base
    });
    if (response?.state) setBackendState(response.state);
    if (response?.results) setResults(response.results);
  };

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { id: `${Date.now()}-user`, role: "user", text: trimmed }]);
    setInput("");

    const response = await sendUserMessage({
      text: trimmed, stage: "done", zip, radius,
      dealer_ids: selectedDealerIds, state: backendState
    });
    if (!response) {
      addBotPrompt(["I couldn't reach the search service just now — please try that again."]);
      return;
    }
    if (response.state) setBackendState(response.state);
    if (response.results) setResults(response.results);
    if (response.bot_response) addBotPrompt([response.bot_response]);
  };

  // ---- Splash while the auth session resolves (avoids landing/tool flash) ----
  if (account.configured && !account.ready) {
    return (
      <div className="splash">
        <span className="splash-mark">Axle</span>
      </div>
    );
  }

  // ---- Hero landing (logged out / not yet entered) ----
  if (!entered) {
    return <LandingPage onEnter={handleEnter} />;
  }

  // ---- Location step ----
  if (!showPanels) {
    return (
      <div className="page">
        <TopBar view={view} onSetView={setView} showSaved={false} />
        <BrandHeader />
        <LocationPicker onProceed={handleProceed} />
      </div>
    );
  }

  const showingSaved = view === "saved";
  const stageResults = showingSaved ? account.savedList : results;

  // ---- Browse step (chat + results) ----
  return (
    <div className="page">
      <TopBar view={view} onSetView={setView} showSaved={true} />
      <BrandHeader />

      <main className="content">
        <div className="chat-rail">
          <section className="chat-card">
            <div className="chat-header">
              <div>
                <h2>Chat with Axle</h2>
                <p>Tell Axle what you want — it ranks the lot in real time.</p>
              </div>
              <div className="chat-status">
                <span className="status-dot status-done" />
                <span>Browsing inventory</span>
              </div>
            </div>

            <div className="summary-strip">
              <span className="summary-title">Captured parameters</span>
              {selectedDealerships.length > 0 && (
                <div className="summary-dealers">
                  <span className="summary-dealer">
                    <strong>📍 {selectedDealerships.length} dealership{selectedDealerships.length === 1 ? "" : "s"}</strong>
                    <em>within {radius} mi of {zip}</em>
                  </span>
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
                              if (e.key === "Enter") handleUpdateCreditScore(tempCreditScore);
                              else if (e.key === "Escape") { setEditingCreditScore(false); setTempCreditScore(""); setCreditError(""); }
                            }}
                            autoFocus
                            placeholder="300-850"
                            style={{ width: "64px", padding: "2px 6px", border: "1px solid var(--accent)", borderRadius: "4px", fontSize: "0.9em", fontFamily: "inherit" }}
                          />
                          <button onClick={() => handleUpdateCreditScore(tempCreditScore)} className="filter-edit-ok">✓</button>
                          <button onClick={() => { setEditingCreditScore(false); setTempCreditScore(""); setCreditError(""); }} className="filter-edit-cancel">✕</button>
                        </>
                      ) : (
                        <>
                          <span className="filter-label">{filter.label}:</span>
                          <span
                            className="filter-value"
                            style={filter.key === "credit_score" ? { cursor: "pointer", textDecoration: "underline", textDecorationStyle: "dotted" } : {}}
                            onClick={() => {
                              if (filter.key === "credit_score") {
                                setEditingCreditScore(true);
                                setTempCreditScore(filter.value.toString());
                                setCreditError("");
                              }
                            }}
                          >
                            {filter.displayValue}
                          </span>
                          <button className="filter-remove" onClick={() => handleRemoveFilter(filter.key)} aria-label={`Remove ${filter.label} filter`}>×</button>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <span className="summary-empty">No parameters captured yet.</span>
              )}
              {creditError && <span className="field-error" role="alert">{creditError}</span>}
            </div>

            <MessageList messages={messages} />
            <Composer value={input} onChange={setInput} onSend={handleSend} stage="done" inputRef={inputRef} />
          </section>
        </div>

        <section className="results-stage">
          {compareNotice && <div className="inline-notice" role="status">{compareNotice}</div>}
          {showingSaved && stageResults.length === 0 && (
            <div className="inline-notice" role="status">
              No saved cars yet — tap the ♥ on any car to save it here.
            </div>
          )}
          <ResultsShell
            results={stageResults}
            selectedCars={selectedCars}
            onToggleCompare={handleToggleCompare}
            hasPreferences={showingSaved ? false : hasPreferences}
            onToggleSave={handleToggleSave}
            isSaved={account.isSaved}
            title={showingSaved ? "Saved cars" : undefined}
          />
        </section>
      </main>

      <ComparisonPanel
        cars={selectedCars}
        isOpen={showComparison}
        onClose={() => setShowComparison(false)}
        onOpenInsights={() => setShowInsightPanel(true)}
      />
      <ComparisonInsightPanel
        cars={selectedCars}
        isOpen={showInsightPanel}
        onClose={() => setShowInsightPanel(false)}
      />
    </div>
  );
}
