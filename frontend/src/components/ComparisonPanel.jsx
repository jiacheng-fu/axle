import React, { useState, useEffect, useRef } from "react";

export default function ComparisonPanel({ cars, onClose, isOpen, onOpenInsights }) {
  const [aiInsight, setAiInsight] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [imageIndices, setImageIndices] = useState({ 0: 0, 1: 0 });
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

  const handlePrevImage = (carIndex) => {
    const car = cars[carIndex];
    const imageCount = car.image_urls?.length || 0;
    if (imageCount > 1) {
      setImageIndices(prev => ({
        ...prev,
        [carIndex]: ((prev[carIndex] || 0) - 1 + imageCount) % imageCount
      }));
    }
  };

  const handleNextImage = (carIndex) => {
    const car = cars[carIndex];
    const imageCount = car.image_urls?.length || 0;
    if (imageCount > 1) {
      setImageIndices(prev => ({
        ...prev,
        [carIndex]: ((prev[carIndex] || 0) + 1) % imageCount
      }));
    }
  };

  const renderCarColumn = (car, carIndex) => {
    if (!car) return null;

    const images = car.image_urls || [];
    const currentIndex = imageIndices[carIndex] || 0;
    const currentImage = images[currentIndex];
    const hasMultipleImages = images.length > 1;

    return (
      <div style={{
        flex: 1,
        padding: "40px",
        overflowY: "auto",
        borderRight: carIndex === 0 ? "2px solid var(--line)" : "none"
      }}>
        <h3 style={{ marginTop: 0, fontSize: "1.5em", marginBottom: "24px" }}>
          {car.year} {car.make} {car.model}
          {car.trim && <span style={{
            marginLeft: "8px",
            fontSize: "0.8em",
            background: "var(--paper-2)",
            padding: "4px 8px",
            borderRadius: "4px"
          }}>{car.trim}</span>}
        </h3>

        {/* Image Gallery */}
        <div style={{ position: "relative", marginBottom: "24px" }}>
          {currentImage ? (
            <img
              src={currentImage}
              alt={`${car.year} ${car.model}`}
              style={{
                width: "100%",
                height: "300px",
                objectFit: "contain",
                borderRadius: "8px",
                background: "var(--paper-2)"
              }}
            />
          ) : (
            <div style={{
              width: "100%",
              height: "300px",
              background: "var(--paper-2)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--muted)"
            }}>
              No image
            </div>
          )}

          {hasMultipleImages && (
            <>
              <button
                onClick={() => handlePrevImage(carIndex)}
                style={{
                  position: "absolute",
                  left: "8px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "rgba(0, 0, 0, 0.6)",
                  color: "white",
                  border: "none",
                  borderRadius: "50%",
                  width: "32px",
                  height: "32px",
                  cursor: "pointer",
                  fontSize: "18px"
                }}
              >
                ‹
              </button>
              <button
                onClick={() => handleNextImage(carIndex)}
                style={{
                  position: "absolute",
                  right: "8px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "rgba(0, 0, 0, 0.6)",
                  color: "white",
                  border: "none",
                  borderRadius: "50%",
                  width: "32px",
                  height: "32px",
                  cursor: "pointer",
                  fontSize: "18px"
                }}
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
                padding: "4px 8px",
                borderRadius: "8px",
                fontSize: "11px"
              }}>
                {currentIndex + 1} / {images.length}
              </div>
            </>
          )}
        </div>

        {/* Price and Basic Info */}
        <div style={{ marginBottom: "28px" }}>
          {car.price && (
            <div style={{ fontSize: "1.8em", fontWeight: "bold", marginBottom: "12px" }}>
              ${car.price.toLocaleString()}
            </div>
          )}
          {car.monthly_payment !== undefined && car.monthly_payment > 0 && (
            <div style={{ fontSize: "1.2em", color: "var(--red)", fontWeight: "600" }}>
              ${car.monthly_payment.toLocaleString()}/mo
              {car.financing_info && (
                <span style={{ fontSize: "0.8em", color: "var(--muted)", fontWeight: "normal", marginLeft: "10px" }}>
                  {car.financing_info.apr_percent}% APR · {car.financing_info.term_months} mo
                </span>
              )}
            </div>
          )}
        </div>

        {/* Specs Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "20px",
          marginBottom: "28px",
          fontSize: "1em"
        }}>
          {car.mileage && (
            <div>
              <strong>Mileage:</strong>
              <div>{car.mileage.toLocaleString()} miles</div>
            </div>
          )}
          {car.exterior_color && (
            <div>
              <strong>Exterior:</strong>
              <div>{car.exterior_color}</div>
            </div>
          )}
          {car.interior_color && (
            <div>
              <strong>Interior:</strong>
              <div>{car.interior_color}</div>
            </div>
          )}
          {car.body_style && (
            <div>
              <strong>Body Style:</strong>
              <div>{car.body_style}</div>
            </div>
          )}
          {car.drivetrain && (
            <div>
              <strong>Drivetrain:</strong>
              <div>{car.drivetrain}</div>
            </div>
          )}
          {car.horsepower && (
            <div>
              <strong>Horsepower:</strong>
              <div>{car.horsepower} hp</div>
            </div>
          )}
          {car.torque_lbft && (
            <div>
              <strong>Torque:</strong>
              <div>{car.torque_lbft} lb-ft</div>
            </div>
          )}
          {car.engine && (
            <div>
              <strong>Engine:</strong>
              <div>{car.engine}</div>
            </div>
          )}
          {car.transmission && (
            <div>
              <strong>Transmission:</strong>
              <div>{car.transmission}</div>
            </div>
          )}
          {car.fuel_type && (
            <div>
              <strong>Fuel Type:</strong>
              <div>{car.fuel_type}</div>
            </div>
          )}
          {(car.mpg_city || car.mpg_highway) && (
            <div>
              <strong>MPG:</strong>
              <div>{car.mpg_city || "—"} city / {car.mpg_highway || "—"} hwy</div>
            </div>
          )}
          {car.seating_capacity && (
            <div>
              <strong>Seating:</strong>
              <div>{car.seating_capacity} passengers</div>
            </div>
          )}
        </div>

        {/* Features */}
        {car.all_features && car.all_features.length > 0 && (
          <div style={{ marginBottom: "24px" }}>
            <strong style={{ display: "block", marginBottom: "12px", fontSize: "1em" }}>Features:</strong>
            <ul style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              fontSize: "0.9em",
              display: "grid",
              gridTemplateColumns: "1fr",
              gap: "6px"
            }}>
              {car.all_features.slice(0, 10).map((feature, i) => (
                <li key={i} style={{ padding: "6px 0" }}>• {feature}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Dealer Notes */}
        {car.dealer_notes && (
          <div style={{
            marginTop: "24px",
            padding: "16px",
            background: "var(--paper)",
            borderRadius: "8px",
            fontSize: "0.9em"
          }}>
            <strong style={{ display: "block", marginBottom: "8px", fontSize: "1em" }}>Dealer Notes:</strong>
            <div style={{ lineHeight: "1.6" }}>{car.dealer_notes}</div>
          </div>
        )}
      </div>
    );
  };

  if (!car1 || !car2) return null;

  return (
    <div style={{
      position: "fixed",
      right: isOpen ? 0 : "-100%",
      top: 0,
      width: "100%",
      height: "100vh",
      background: "var(--paper)",
      transition: "right 0.3s ease-in-out",
      zIndex: 1000,
      display: "flex",
      flexDirection: "column"
    }}>
      {/* Header */}
      <div style={{
        padding: "20px",
        borderBottom: "1px solid var(--line)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: "var(--red)",
        color: "white"
      }}>
        <h2 style={{ margin: 0, fontSize: "1.5em" }}>Vehicle Comparison</h2>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <button
            onClick={onOpenInsights}
            style={{
              background: "white",
              border: "2px solid white",
              color: "var(--red)",
              fontSize: "1em",
              cursor: "pointer",
              borderRadius: "4px",
              padding: "8px 16px",
              fontWeight: "600"
            }}
          >
            View AI Insights
          </button>
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
      </div>

      {/* Split Car View */}
      <div style={{
        display: "flex",
        flex: 1,
        overflowY: "auto"
      }}>
        {renderCarColumn(car1, 0)}
        {renderCarColumn(car2, 1)}
      </div>
    </div>
  );
}
