import React, { useState } from "react";

export default function CarCard({ car }) {
  return (
    <div
      style={{
        background: "var(--card)",
        borderRadius: 16,
        padding: "1.5rem",
        boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
        transition: "transform .2s ease"
      }}
    >
      <h3 style={{ marginBottom: ".25rem" }}>
        {car.year} {car.make} {car.model}
      </h3>

      <p style={{ color: "var(--muted)", fontSize: ".9rem" }}>
        {car.engine} • {car.fuel_type}
      </p>

      <div style={{ marginTop: "1rem", fontSize: ".9rem" }}>
        <strong>Age:</strong> {car.age} years
      </div>

      <div
        style={{
          marginTop: "1.25rem",
          fontSize: ".75rem",
          color: "var(--muted)",
          letterSpacing: ".04em"
        }}
      >
        VIN {car.vin}
      </div>
    </div>
  );
}
