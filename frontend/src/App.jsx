import React, { useState } from "react";

import VinInput from "./components/VinInput";
import CarCard from "./components/CarCard";
import ComparisonPanel from "./components/ComparisonPanel";
import SkeletonCard from "./components/SkeletonCard";

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleCompare(vins) {
    setLoading(true);

    try {
      // dynamic import of the small hook that calls backend
      const mod = await import("./hooks/useCompareCars.js");
      const res = await mod.compareCars(vins);
      setData(res);
    } catch (err) {
      // fallback demo data for presentation when backend isn't running
      setData({
        cars: vins.slice(0, 3).map((v, i) => ({
          vin: v || `VIN${i}`,
          year: i === 0 ? "2019" : i === 1 ? "2018" : "2017",
          make: "Toyota",
          model: i === 0 ? "Camry" : i === 1 ? "RAV4" : "Corolla",
          engine: "2.5L I4",
          fuel_type: "Gasoline",
          age: i === 0 ? 5 : i === 1 ? 6 : 7,
          price_estimate: i === 0 ? 18000 : i === 1 ? 15000 : 12000,
          reliability_score: i === 0 ? 78 : i === 1 ? 72 : 75
        })),
        ai_summary: "Demo: Camry recommended for commuters, RAV4 for space, Corolla for budget buyers."
      });
    } finally {
      setLoading(false);
    }
  }

  function exportCSV() {
    if (!data || !data.cars) return;
    const rows = [
      ["vin", "year", "make", "model", "price_estimate", "reliability_score"],
      ...data.cars.map(c => [c.vin, c.year || '', c.make||'', c.model||'', c.price_estimate||'', c.reliability_score||''])
    ];
    const csv = rows.map(r => r.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'comparison.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">Used Car Intelligence</h1>
        <p className="app-subtitle">VIN-powered insights for smarter dealership decisions</p>
      </header>

      <VinInput onSubmit={handleCompare} />

      {loading && <div className="loading">Analyzing vehicles...</div>}

      {data && (
        <section className="compare-section fade-up">
          <div>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
              <div>
                <span className="meta-badge">Avg price: ${Math.round((data.cars.reduce((s,c)=>s+(c.price_estimate||0),0)||0)/data.cars.length||0)}</span>
                <span className="meta-badge">Avg reliability: {Math.round((data.cars.reduce((s,c)=>s+(c.reliability_score||0),0)||0)/data.cars.length||0)}</span>
              </div>
              <div>
                <button className="btn-primary" onClick={exportCSV}>Export CSV</button>
              </div>
            </div>

            <div className="cards-grid" style={{marginTop:16}}>
              {loading
                ? [0,1,2].map(i=> <SkeletonCard key={i} />)
                : data.cars.map((car) => (
                    <CarCard key={car.vin} car={car} />
                  ))}
            </div>
          </div>

          <ComparisonPanel summary={data.ai_summary} />
        </section>
      )}
    </div>
  );
}
