import React from "react";

function GoogleG() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.1 29.5 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.3C29.2 35 26.7 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.5 5C9.6 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4 5.5l6.3 5.3C41.8 35.7 44 30.3 44 24c0-1.3-.1-2.3-.4-3.5z" />
    </svg>
  );
}

export default function LandingPage({ onEnter }) {
  return (
    <div className="landing">
      {/* Hero — full-screen video with a light brand veil */}
      <section className="landing-hero">
        <div className="landing-bg" aria-hidden="true">
          <video className="landing-video" autoPlay muted loop playsInline poster="/landing-bg.jpg">
            <source src="/landing-bg.mp4" type="video/mp4" />
          </video>
        </div>

        <div className="landing-hero-inner">
          <h1 className="landing-title">
            Just tell us what
            <br />
            you want. <em>We'll find it.</em>
          </h1>
          <p className="landing-sub">
            The classic car-salesman experience, reimagined online — describe your next car the
            way you'd say it out loud. No filters, no spec sheets, no homework.
          </p>
          <div className="landing-cta">
            <button className="btn-google btn-google-lg" type="button" onClick={onEnter}>
              <GoogleG /> Sign in with Google
            </button>
            <span className="landing-note">Free · takes a second · we only save the cars you pick.</span>
          </div>
        </div>

        <div className="scroll-hint" aria-hidden="true">
          <span>Scroll</span>
          <span className="scroll-arrow">↓</span>
        </div>
      </section>

      {/* Value props */}
      <section className="landing-section landing-values">
        <ul className="landing-features">
          <li>
            <strong>Talk, don't filter</strong>
            <span>Say it like you'd tell a salesman — “roomy, reliable, under $30k.” No dropdowns.</span>
          </li>
          <li>
            <strong>We sweat the specs</strong>
            <span>Real cars, real specs near you — matched to what you actually care about.</span>
          </li>
          <li>
            <strong>Save &amp; compare</strong>
            <span>Heart the ones you like and line them up side by side.</span>
          </li>
        </ul>
      </section>

      {/* How it works */}
      <section className="landing-section landing-how">
        <span className="landing-eyebrow">How it works</span>
        <ol className="landing-steps">
          <li>
            <span className="step-num">1</span>
            <div>
              <strong>Say what you want</strong>
              <p>Type it in plain English — your budget, your life, your must-haves. No jargon required.</p>
            </div>
          </li>
          <li>
            <span className="step-num">2</span>
            <div>
              <strong>We do the legwork</strong>
              <p>Axle searches real dealer inventory near you and ranks it to what you actually said.</p>
            </div>
          </li>
          <li>
            <span className="step-num">3</span>
            <div>
              <strong>Shortlist &amp; decide</strong>
              <p>Heart the ones you love, compare them side by side, and walk in knowing exactly what you want.</p>
            </div>
          </li>
        </ol>
      </section>

      {/* Closing CTA */}
      <section className="landing-section landing-closing">
        <div className="landing-closing-inner">
          <h2 className="landing-closing-title">
            Stop opening twenty tabs.
            <br />
            <em>Just start talking.</em>
          </h2>
          <p className="landing-closing-sub">Axle does the digging — you pick the winner.</p>
          <button className="btn-google btn-google-lg" type="button" onClick={onEnter}>
            <GoogleG /> Sign in with Google
          </button>
        </div>
      </section>
    </div>
  );
}
