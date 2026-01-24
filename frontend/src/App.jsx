import React, { useState } from "react";

import VinInput from "./components/VinInput";
import CarCard from "./components/CarCard";
import ComparisonPanel from "./components/ComparisonPanel";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleCompare(vins) {
    setLoading(true);

    setTimeout(() => {
      setData({
        cars: [
          {
            vin: "1FTYR3XM2HKA46643",
            year: "2019",
            make: "Toyota",
            model: "Camry",
            engine: "2.5L I4",
            fuel_type: "Gasoline",
            age: 5
          },
          {
            vin: "JTMBFREV0JD123456",
            year: "2018",
            make: "Toyota",
            model: "RAV4",
            engine: "2.5L I4",
            fuel_type: "Gasoline",
            age: 6
          }
        ],
        ai_summary: `Toyota Camry (2019) vs RAV4 (2018)

• Camry: Better efficiency, lower depreciation
• RAV4: More space, stronger resale

Recommendation:
Camry for commuters, RAV4 for versatility.`
      });
      setLoading(false);
    }, 1200);
  }

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "3rem" }}>
      <header style={{ marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "2.8rem", fontWeight: 700 }}>
          Used Car Intelligence
        </h1>
        <p style={{ color: "var(--muted)", marginTop: ".5rem" }}>
          VIN-powered insights for smarter dealership decisions
        </p>
      </header>

      <VinInput onSubmit={handleCompare} />

      {loading && (
        <div style={{ marginTop: "2rem", color: "var(--muted)" }}>
          Analyzing vehicles...
        </div>
      )}

      {data && (
        <>
          <section
            style={{
              marginTop: "3rem",
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: "2rem"
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                gap: "1.5rem"
              }}
            >
              {data.cars.map((car) => (
                <CarCard key={car.vin} car={car} />
              ))}
            </div>

            <ComparisonPanel summary={data.ai_summary} />
          </section>
        </>
      )}
    </div>
  );
}
