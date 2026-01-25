import React from "react";

export default function BrandHeader() {
  return (
    <header className="hero">
      <div className="hero-badge">Toyota-inspired</div>
      <h1 className="hero-title">Redline Used Car Scout</h1>
      <p className="hero-subtitle">
        Tell us your zip code, then add the features you want. We will keep
        listening until you are ready to see results.
      </p>
      <div className="hero-strip" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </header>
  );
}
