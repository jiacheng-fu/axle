import React, { useCallback } from "react";

export default function Composer({ value, onChange, onSend, stage, inputRef }) {
  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  const isZip = stage === "zip";

  return (
    <div className="composer">
      <label className="composer-label" htmlFor="chat-input">
        {isZip ? "Enter your zip code" : "Refine your search"}
      </label>
      <textarea
        id="chat-input"
        className="composer-input"
        ref={inputRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          isZip ? "e.g. 77840" : "e.g. Toyota SUV under $25k, AWD, Apple CarPlay, finance with $5k down"
        }
        rows={2}
      />
      <div className="composer-actions">
        <button className="btn-primary" type="button" onClick={onSend}>
          {isZip ? "Search" : "Send"}
        </button>
      </div>
      <p className="composer-hint">
        {isZip
          ? "Enter a 5-digit US zip to find dealers nearby."
          : "Press Enter to send. Shift + Enter for a new line."}
      </p>
    </div>
  );
}
