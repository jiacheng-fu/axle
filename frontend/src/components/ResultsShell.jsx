import React, { useState } from "react";

export default function ResultsShell({ results = [], selectedCars = [], onToggleCompare }) {
  // Track current image index for each result item
  const [imageIndices, setImageIndices] = useState({});

  const hasRelaxations = results.length > 0 && results[0].relaxations && results[0].relaxations.length > 0;

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
      <h2>Results {results.length > 0 && `(${results.length})`}</h2>

      {hasRelaxations && (
        <div style={{
          padding: "12px 16px",
          background: "rgba(255, 193, 7, 0.1)",
          border: "1px solid rgba(255, 193, 7, 0.3)",
          borderRadius: "8px",
          marginBottom: "16px"
        }}>
          <strong style={{ color: "#ffc107" }}>⚠ Constraints Relaxed</strong>
          <ul style={{ margin: "8px 0 0 0", paddingLeft: "20px", fontSize: "0.9em" }}>
            {results[0].relaxations.map((relaxation, i) => (
              <li key={i} style={{ color: "#ffc107" }}>{relaxation}</li>
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
                    <span className="match-score" style={{
                      color: item.match_score_percent >= 75 ? "#4caf50" :
                             item.match_score_percent >= 50 ? "#ffc107" : "#ff9800"
                    }}>
                      {item.match_score_percent}% match
                    </span>
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
                            <span style={{ fontStyle: "italic", color: "#666" }}>
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
                                  color: "#666",
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

                    {item.match_reasons && item.match_reasons.length > 0 && (
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

                    {item.source_url && (
                      <div style={{ marginTop: "16px" }}>
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            color: "var(--red)",
                            textDecoration: "none",
                            fontSize: "0.95em",
                            fontWeight: "600",
                            display: "inline-block"
                          }}
                        >
                          View Full Listing →
                        </a>
                      </div>
                    )}

                    {onToggleCompare && (
                      <button
                        className="btn-compare"
                        onClick={() => onToggleCompare(item)}
                        style={{
                          marginTop: "16px",
                          padding: "10px 20px",
                          border: selectedCars.some(car => car.id === item.id) ? "2px solid var(--red)" : "2px solid #ddd",
                          borderRadius: "6px",
                          background: selectedCars.some(car => car.id === item.id) ? "var(--red)" : "white",
                          color: selectedCars.some(car => car.id === item.id) ? "white" : "#333",
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
            Ranked car matches will appear here once you provide your preferences and click "Show Results".
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
