import React, { useState } from "react";

export default function VinInput({ onSubmit }) {
  const [value, setValue] = useState("");

  return (
    <div style={styles.container}>
      <textarea
        placeholder="Enter VINs (one per line)"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={styles.textarea}
      />
      <button
        style={styles.button}
        onClick={() => onSubmit(value.split("\n").filter(Boolean))}
      >
        Compare Vehicles
      </button>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "600px",
    marginTop: "1.5rem"
  },
  textarea: {
    width: "100%",
    height: "100px",
    padding: "1rem",
    borderRadius: "8px",
    border: "1px solid #ccc",
    fontSize: "1rem"
  },
  button: {
    marginTop: "1rem",
    padding: "0.75rem 1.5rem",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#c8102e",
    color: "white",
    fontSize: "1rem",
    cursor: "pointer"
  }
};
