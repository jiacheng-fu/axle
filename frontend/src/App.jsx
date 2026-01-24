import React, { useState } from "react";
import VinInput from "./components/VinInput";
import CarCard from "./components/CarCard";
import ComparisonPanel from "./components/ComparisonPanel";


export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleCompare(vins) {
    setLoading(true);

    // 🔥 MOCK DATA (safe for demo)
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
        ai_summary: `✅ Toyota Camry (2019)
Pros:
- Better fuel economy
- Lower depreciation
- Proven reliability

Cons:
- Less cargo space

✅ Toyota RAV4 (2018)
Pros:
- Higher resale value
- AWD availability
- More cargo room

⚖️ Final Verdict:
Choose the Camry for commuting efficiency.
Choose the RAV4 for versatility and resale value.`
      });
      setLoading(false);
    }, 1200);
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Used Car Intelligence</h1>
      <p style={styles.subtitle}>
        Compare used cars using VIN data and AI-powered insights
      </p>

      <VinInput onSubmit={handleCompare} />

      {loading && <p style={styles.loading}>Analyzing vehicles...</p>}

      {data && (
        <>
          <div style={styles.cardGrid}>
            {data.cars.map((car) => (
              <CarCard key={car.vin} car={car} />
            ))}
          </div>
          <ComparisonPanel summary={data.ai_summary} />
        </>
      )}
    </div>
  );
}

const styles = {
  page: {
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont",
    padding: "3rem",
    background: "#f8f9fb",
    minHeight: "100vh"
  },
  title: {
    fontSize: "2.5rem",
    fontWeight: "700",
    color: "#c8102e" // Toyota red
  },
  subtitle: {
    color: "#555",
    marginBottom: "2rem"
  },
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "1.5rem",
    marginTop: "2rem"
  },
  loading: {
    marginTop: "2rem",
    fontWeight: "600"
  }
};
