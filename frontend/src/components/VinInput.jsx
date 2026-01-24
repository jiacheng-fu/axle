import React, { useState } from "react";

export default function VinInput({ onSubmit }) {
  const [value, setValue] = useState("");

  return (
    <div className="vin-input">
      <textarea
        className="vin-textarea"
        placeholder="Enter VINs (one per line)"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />

      <div style={{display:'flex', gap:8, marginTop:12, alignItems:'center'}}>
        <button
          className="btn-primary"
          onClick={() => onSubmit(value.split("\n").filter(Boolean))}
        >
          Compare Vehicles
        </button>

        <button
          onClick={() => setValue('')}
          style={{background:'transparent', border:'1px solid var(--glass-border)', padding:'0.6rem 1rem', borderRadius:999}}
        >
          Clear
        </button>

        <div style={{marginLeft: 'auto', display:'flex', gap:8}}>
          <button onClick={() => setValue('1FTYR3XM2HKA46643\nJTMBFREV0JD123456')} style={{background:'transparent', border:'none', color:'var(--muted)'}}>Use example VINs</button>
        </div>
      </div>
    </div>
  );
}
