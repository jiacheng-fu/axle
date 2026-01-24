import React, { useState } from "react";
export default function ComparisonPanel({ summary }) {
  return (
    <div style={styles.panel}>
      <h2 style={styles.title}>AI Recommendation</h2>
      <pre style={styles.text}>{summary}</pre>
    </div>
  );
}

const styles = {
  panel: {
    marginTop: "3rem",
    background: "#111",
    color: "#0f0",
    padding: "2rem",
    borderRadius: "12px",
    fontSize: "0.9rem"
  },
  title: {
    color: "#fff",
    marginBottom: "1rem"
  },
  text: {
    whiteSpace: "pre-wrap"
  }
};
