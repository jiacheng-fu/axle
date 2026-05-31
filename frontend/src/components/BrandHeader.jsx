import React from "react";

export default function BrandHeader() {
  return (
    <header className="hero">
      <span className="hero-badge">Your car salesman, online</span>
      <h1 className="hero-title">
        Car<em>Scout</em>
      </h1>
      <p className="hero-subtitle">
        Tell us your zip code, then describe the car you want in plain words.
        We listen, search, and rank real listings — until you're ready to see them.
      </p>
      <div className="hero-strip" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </header>
  );
}
