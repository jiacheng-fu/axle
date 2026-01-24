import React, { useState } from "react";

export default function VinInput({ onSubmit }) {
  const [value, setValue] = useState("");

  return (
    <div style={{ maxWidth: 520 }}>
      <textarea
        placeholder="Enter VINs (one per line)"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={{
          width: "100%",
          height: 110,
          padding: "1rem",
          borderRadius: 12,
          border: "1px solid #e5e7eb",
          fontSize: "1rem",
          resize: "none"
        }}
      />

      <button
        onClick={() => onSubmit(value.split("\n").filter(Boolean))}
        style={{
          marginTop: "1rem",
          background: "var(--accent)",
          color: "white",
          padding: "0.75rem 1.75rem",
          borderRadius: 999,
          border: "none",
          fontSize: "1rem",
          fontWeight: 600
        }}
      >
        Compare Vehicles
      </button>
    </div>
  );
}
