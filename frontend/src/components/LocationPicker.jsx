import React, { useEffect, useMemo, useRef, useState } from "react";
import { fetchDealers } from "../api/client.js";

const RADIUS_MIN = 5;
const RADIUS_MAX = 250;
const dealerKey = (d) => d.id || `${d.name}__${d.address}`;

export default function LocationPicker({ onProceed }) {
  const [zipInput, setZipInput] = useState("");
  const [zip, setZip] = useState(null);
  const [radius, setRadius] = useState(50);
  const [dealers, setDealers] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const debounceRef = useRef(null);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  const load = async (z, r) => {
    setLoading(true);
    setError("");
    const res = await fetchDealers(z, r);
    setLoading(false);
    if (!res) {
      setError("Couldn't reach the search service — please try again.");
      return;
    }
    if (!res.valid) {
      setError(res.error || "Please enter a valid 5-digit US zip code.");
      setDealers([]);
      return;
    }
    setDealers(res.dealers || []);
    setSelectedIds((res.dealers || []).map(dealerKey)); // default: all selected
  };

  const handleSearch = () => {
    const z = zipInput.trim();
    if (!/^\d{5}$/.test(z)) {
      setError("Enter a 5-digit US zip code.");
      return;
    }
    setZip(z);
    load(z, radius);
  };

  // Re-fetch as the radius slider moves (debounced), once a zip is locked in.
  useEffect(() => {
    if (!zip) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => load(zip, radius), 300);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [radius]);

  const toggle = (id) =>
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const proceed = () => {
    const chosen = dealers.filter((d) => selectedSet.has(dealerKey(d)));
    if (!zip || chosen.length === 0) return;
    onProceed({ zip, radius, dealerIds: chosen.map(dealerKey), dealers: chosen });
  };

  // Fill % for the slider track gradient.
  const fillPct = ((radius - RADIUS_MIN) / (RADIUS_MAX - RADIUS_MIN)) * 100;

  return (
    <section className="locator-solo">
      <div className="locator-panel">
        <span className="hero-badge">Step 1 · Location</span>
        <h2 className="locator-title">Where are you shopping?</h2>
        <p className="locator-sub">
          Enter a US zip and choose how far you'll travel. We'll find every dealer in range.
        </p>

        <div className="locator-zip">
          <input
            className="composer-input"
            value={zipInput}
            onChange={(e) => setZipInput(e.target.value.replace(/[^\d]/g, "").slice(0, 5))}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="e.g. 78750"
            inputMode="numeric"
            aria-label="Zip code"
          />
          <button className="btn-primary" type="button" onClick={handleSearch}>
            Search
          </button>
        </div>
        {error && <span className="field-error" role="alert">{error}</span>}

        <div className={`radius-slider ${zip ? "" : "is-disabled"}`}>
          <div className="radius-slider-head">
            <span className="flow-panel-label">Search radius</span>
            <strong className="radius-value">{radius} mi</strong>
          </div>
          <input
            type="range"
            min={RADIUS_MIN}
            max={RADIUS_MAX}
            step={1}
            value={radius}
            onChange={(e) => setRadius(Number(e.target.value))}
            disabled={!zip}
            aria-label="Search radius in miles"
            style={{
              background: `linear-gradient(90deg, var(--accent) ${fillPct}%, var(--line) ${fillPct}%)`,
            }}
          />
          <div className="radius-scale">
            <span>{RADIUS_MIN} mi</span>
            <span>{RADIUS_MAX} mi</span>
          </div>
        </div>

        <div className="dealer-head">
          <span className="flow-panel-label">
            {loading
              ? "Searching…"
              : zip
              ? `${dealers.length} dealer${dealers.length === 1 ? "" : "s"} within ${radius} mi`
              : "Dealers"}
          </span>
          {dealers.length > 0 && (
            <span className="dealer-bulk">
              <button type="button" onClick={() => setSelectedIds(dealers.map(dealerKey))}>All</button>
              <span aria-hidden="true">·</span>
              <button type="button" onClick={() => setSelectedIds([])}>None</button>
            </span>
          )}
        </div>

        <div className="dealer-scroll">
          {!zip && <p className="flow-panel-hint">Search a zip to see dealers in range.</p>}
          {zip && !loading && dealers.length === 0 && (
            <p className="flow-panel-hint">No dealers within {radius} mi — try a larger radius.</p>
          )}
          {dealers.map((d) => {
            const id = dealerKey(d);
            const active = selectedSet.has(id);
            return (
              <button
                key={id}
                type="button"
                className={`dealer-row ${active ? "is-active" : ""}`}
                onClick={() => toggle(id)}
                aria-pressed={active}
              >
                <span className="dealer-check" aria-hidden="true">{active ? "✓" : ""}</span>
                <span className="dealer-row-info">
                  <span className="dealer-name">{d.name}</span>
                  <span className="dealer-meta">
                    {[d.city, d.state].filter(Boolean).join(", ")}
                    {d.inventory_count ? ` · ${d.inventory_count} listed` : ""}
                  </span>
                </span>
                {d.distance && <span className="dealer-distance">{d.distance}</span>}
              </button>
            );
          })}
        </div>

        <button
          className="btn-primary locator-proceed"
          type="button"
          disabled={selectedIds.length === 0}
          onClick={proceed}
        >
          Browse {selectedIds.length || ""} dealer{selectedIds.length === 1 ? "" : "s"} →
        </button>
      </div>
    </section>
  );
}
