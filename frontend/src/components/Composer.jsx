import React, { useCallback } from "react";

export default function Composer({
  value,
  onChange,
  onSend,
  onShowResults,
  canShowResults,
  stage,
  inputRef
}) {
  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  return (
    <div className="composer">
      <label className="composer-label" htmlFor="chat-input">
        {stage === "zip"
          ? "Enter your zip code"
          : "Add a preference or feature"}
      </label>
      <textarea
        id="chat-input"
        className="composer-input"
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          stage === "zip"
            ? "e.g. 77840"
            : "e.g. Toyota, under $15k, Apple CarPlay, AWD"
        }
        rows={2}
      />
      <div className="composer-actions">
        <button className="btn-primary" type="button" onClick={onSend}>
          Send
        </button>
        <button
          className="btn-ghost"
          type="button"
          onClick={onShowResults}
          disabled={!canShowResults}
        >
          Show me my results
        </button>
      </div>
      <p className="composer-hint">
        Press Enter to send. Shift + Enter for a new line.
      </p>
    </div>
  );
}
