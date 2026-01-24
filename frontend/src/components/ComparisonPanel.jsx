import React, { useState } from "react";

export default function ComparisonPanel({ summary }) {
  return (
    <aside
      style={{
        background: "#0b0b0c",
        borderRadius: 16,
        padding: "2rem",
        color: "#e5e7eb",
        fontSize: ".95rem"
      }}
    >
      <h2 style={{ marginBottom: "1rem" }}>AI Recommendation</h2>
      <pre
        style={{
          whiteSpace: "pre-wrap",
          fontFamily: "inherit",
          lineHeight: 1.5
        }}
      >
        {summary}
      </pre>
    </aside>
  );
}
