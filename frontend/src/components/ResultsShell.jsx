import React from "react";

export default function ResultsShell({ results = [] }) {
  return (
    <section className="future-panel">
      <h2>Results</h2>
      {results.length ? (
        <div className="results-list">
          {results.map((item, index) => (
            <div key={`${item.year}-${item.model}-${item.trim}-${index}`} className="results-item">
              <span className="results-rank">#{index + 1}</span>
              <div className="results-card">
                <div className="results-media">
                  {item.image_url ? (
                    <img src={item.image_url} alt={`${item.year ?? ""} ${item.model ?? "Vehicle"}`} loading="lazy" />
                  ) : (
                    <div className="results-fallback">No image</div>
                  )}
                </div>
                <div className="results-content">
                  <div className="results-meta">
                    <span className="results-year">{item.year ?? "—"}</span>
                    <span className="results-model">{item.model ?? "Unknown model"}</span>
                    <span className="results-trim">{item.trim ?? "Trim N/A"}</span>
                  </div>
                  <p className="results-notes">
                    {item.dealer_notes || "Dealer description not available."}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <p>
            Ranked car matches will appear here once the backend is connected to
            listings data.
          </p>
          <div className="future-placeholder">
            <div className="placeholder-line" />
            <div className="placeholder-line" />
            <div className="placeholder-line" />
          </div>
        </>
      )}
    </section>
  );
}
