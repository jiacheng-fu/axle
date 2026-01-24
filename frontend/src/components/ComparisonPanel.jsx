import React, { useState } from "react";

export default function ComparisonPanel({ summary }) {
  return (
    <aside className="comparison-panel">
      <h2>AI Recommendation</h2>
      <pre className="ai-summary">{summary}</pre>
    </aside>
  );
}
