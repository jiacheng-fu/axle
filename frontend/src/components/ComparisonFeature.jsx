export default function ComparisonPanel({ summary }) {
  return (
    <div className="ai-panel">
      <h2>AI Recommendation</h2>
      <pre>{summary}</pre>
    </div>
  );
}
