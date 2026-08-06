import React, { useState } from "react";

export default function ResultsShell({ results = [], selectedCars = [], onToggleCompare, hasPreferences = false, onToggleSave, isSaved, title }) {
  // Track current image index for each result item
  const [imageIndices, setImageIndices] = useState({});

  // Match scores / reasons / relaxations are only meaningful once the user has
  // stated preferences. In pure browse mode this is just an inventory listing.
  const hasRelaxations = hasPreferences && results.length > 0 && results[0].relaxations && results[0].relaxations.length > 0;

  const handlePrevImage = (itemIndex, imageCount) => {
    setImageIndices(prev => ({
      ...prev,
      [itemIndex]: ((prev[itemIndex] || 0) - 1 + imageCount) % imageCount
    }));
  };

  const handleNextImage = (itemIndex, imageCount) => {
    setImageIndices(prev => ({
      ...prev,
      [itemIndex]: ((prev[itemIndex] || 0) + 1) % imageCount
    }));
  };

  return (
    <section className="future-panel">
      <h2>
        {title || (hasPreferences ? "Top matches" : "Inventory")} {results.length > 0 && `(${results.length})`}
      </h2>

      {hasRelaxations && (
        <div style={{
          padding: "12px 16px",
          background: "rgba(176, 116, 16, 0.08)",
          border: "1px solid rgba(176, 116, 16, 0.22)",
          borderRadius: "8px",
          marginBottom: "16px"
        }}>
          <strong style={{ color: "var(--amber)" }}>⚠ Constraints Relaxed</strong>
          <ul style={{ margin: "8px 0 0 0", paddingLeft: "20px", fontSize: "0.9em" }}>
            {results[0].relaxations.map((relaxation, i) => (
              <li key={i} style={{ color: "var(--amber)" }}>{relaxation}</li>
            ))}
          </ul>
        </div>
      )}

      {results.length ? (
        <div className="results-list">
          {results.map((item, index) => (
            <div key={`${item.year}-${item.model}-${item.trim}-${index}`} className="results-item">
              <div className="results-card">
                <div className="results-header">
                  <div className="results-rank-badge">
                    <span className="rank-number">#{index + 1}</span>
                    {onToggleSave && (
                      <button
                        type="button"
                        className={`heart-btn ${isSaved && isSaved(item) ? "is-saved" : ""}`}
                        onClick={() => onToggleSave(item)}
                        aria-pressed={isSaved ? isSaved(item) : false}
                        aria-label={isSaved && isSaved(item) ? "Remove from saved" : "Save car"}
                        title={isSaved && isSaved(item) ? "Saved — click to remove" : "Save car"}
                      >
                        {isSaved && isSaved(item) ? "♥" : "♡"}
                      </button>
                    )}
                    {hasPreferences && item.match_score_percent !== undefined && (
                      <span className="match-score" style={{
                        color: item.match_score_percent >= 75 ? "var(--green)" :
                               item.match_score_percent >= 50 ? "var(--amber)" : "var(--accent)"
                      }}>
                        {item.match_score_percent}% match
                      </span>
                    )}
                  </div>
                </div>

                <div className="results-body">
                  <div className="results-media" style={{ position: "relative" }}>
                    {(() => {
                      const images = item.image_urls || [];
                      const currentIndex = imageIndices[index] || 0;
                      const currentImage = images[currentIndex];
                      const hasMultipleImages = images.length > 1;

                      return (
                        <>
                          {currentImage ? (
                            <img src={currentImage} alt={`${item.year ?? ""} ${item.model ?? "Vehicle"}`} loading="lazy" />
                          ) : (
                            <div className="results-fallback">No image</div>
                          )}

                          {hasMultipleImages && (
                            <>
                              <button
                                onClick={() => handlePrevImage(index, images.length)}
                                style={{
                                  position: "absolute",
                                  left: "8px",
                                  top: "50%",
                                  transform: "translateY(-50%)",
                                  background: "rgba(0, 0, 0, 0.6)",
                                  color: "white",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "36px",
                                  height: "36px",
                                  cursor: "pointer",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "20px",
                                  fontWeight: "bold",
                                  transition: "background 0.2s ease",
                                  zIndex: 2
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(0, 0, 0, 0.8)"}
                                onMouseLeave={(e) => e.currentTarget.style.background = "rgba(0, 0, 0, 0.6)"}
                                aria-label="Previous image"
                              >
                                ‹
                              </button>
                              <button
                                onClick={() => handleNextImage(index, images.length)}
                                style={{
                                  position: "absolute",
                                  right: "8px",
                                  top: "50%",
                                  transform: "translateY(-50%)",
                                  background: "rgba(0, 0, 0, 0.6)",
                                  color: "white",
                                  border: "none",
                                  borderRadius: "50%",
                                  width: "36px",
                                  height: "36px",
                                  cursor: "pointer",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "20px",
                                  fontWeight: "bold",
                                  transition: "background 0.2s ease",
                                  zIndex: 2
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(0, 0, 0, 0.8)"}
                                onMouseLeave={(e) => e.currentTarget.style.background = "rgba(0, 0, 0, 0.6)"}
                                aria-label="Next image"
                              >
                                ›
                              </button>
                              <div style={{
                                position: "absolute",
                                bottom: "8px",
                                left: "50%",
                                transform: "translateX(-50%)",
                                background: "rgba(0, 0, 0, 0.6)",
                                color: "white",
                                padding: "4px 12px",
                                borderRadius: "12px",
                                fontSize: "12px",
                                fontWeight: "500",
                                zIndex: 2
                              }}>
                                {currentIndex + 1} / {images.length}
                              </div>
                            </>
                          )}
                        </>
                      );
                    })()}
                  </div>

                  <div className="results-content">
                    <div className="results-title">
                      <h3>
                        {item.year ?? "—"} {item.make ?? ""} {item.model ?? "Unknown"}
                        {item.trim && <span className="trim-badge">{item.trim}</span>}
                      </h3>
                    </div>

                    <div className="results-specs">
                      {item.price && (
                        <div className="spec-item price">
                          <strong>${item.price.toLocaleString()}</strong>
                        </div>
                      )}
                      {item.monthly_payment !== undefined && (
                        <div className="spec-item">
                          {item.monthly_payment === 0 ? (
                            <span style={{ fontStyle: "italic", color: "var(--muted)" }}>
                              Down payment covers full price
                            </span>
                          ) : (
                            <>
                              <span style={{ fontWeight: "700", color: "var(--red)" }}>
                                ${item.monthly_payment.toLocaleString()}/mo
                              </span>
                              {item.financing_info && (
                                <div style={{
                                  fontSize: "0.85em",
                                  color: "var(--muted)",
                                  marginTop: "2px"
                                }}>
                                  {item.financing_info.apr_percent}% APR · {item.financing_info.term_months} months · <span style={{ fontStyle: "italic" }}>Est.</span>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                      {item.mileage && (
                        <div className="spec-item">
                          <span>{item.mileage.toLocaleString()} miles</span>
                        </div>
                      )}
                      {item.horsepower && (
                        <div className="spec-item">
                          <span>{item.horsepower}hp {item.engine && `(${item.engine})`}</span>
                        </div>
                      )}
                      {item.exterior_color && (
                        <div className="spec-item">
                          <span>{item.exterior_color}</span>
                        </div>
                      )}
                      {item.drivetrain && (
                        <div className="spec-item">
                          <span>{item.drivetrain}</span>
                        </div>
                      )}
                    </div>

                    {item.features && item.features.length > 0 && (
                      <div className="results-features">
                        <strong>Key Features:</strong>
                        <ul>
                          {item.features.map((feature, i) => (
                            <li key={i}>{feature}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {hasPreferences && item.match_reasons && item.match_reasons.length > 0 && (
                      <div className="match-reasons">
                        <strong>Why this match:</strong>
                        <ul>
                          {item.match_reasons.slice(0, 5).map((reason, i) => (
                            <li key={i} className={reason.startsWith("✓") ? "reason-good" : "reason-warning"}>
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}


                    {onToggleCompare && (
                      <button
                        className="btn-compare"
                        onClick={() => onToggleCompare(item)}
                        style={{
                          marginTop: "16px",
                          padding: "10px 20px",
                          border: selectedCars.some(car => car.id === item.id) ? "1px solid var(--accent)" : "1px solid var(--line)",
                          borderRadius: "999px",
                          background: selectedCars.some(car => car.id === item.id) ? "var(--accent)" : "var(--card)",
                          color: selectedCars.some(car => car.id === item.id) ? "#fdf6f0" : "var(--ink)",
                          cursor: "pointer",
                          fontSize: "0.95em",
                          fontWeight: "600",
                          width: "100%",
                          transition: "all 0.2s ease"
                        }}
                      >
                        {selectedCars.some(car => car.id === item.id) ? "✓ Selected for Comparison" : "Compare"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <p>
            Vehicles from your selected dealerships will appear here. Tell Axle what you're
            looking for to rank them to your taste.
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
