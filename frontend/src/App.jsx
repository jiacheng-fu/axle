import { useState } from "react";
import { compareCars } from "./hooks/useCompareCars";
import VinInput from "./components/VinInput";
import CarCard from "./components/CarCard";
import ComparisonPanel from "./components/ComparisonPanel";

export default function App() {
  const [data, setData] = useState(null);

  async function handleCompare(vins) {
    const result = await compareCars(vins);
    setData(result);
  }

  return (
    <div>
      <h1>Used Car Intelligence</h1>
      <VinInput onSubmit={handleCompare} />

      {data && (
        <>
          <div className="grid">
            {data.cars.map(car => (
              <CarCard key={car.vin} car={car} />
            ))}
          </div>
          <ComparisonPanel summary={data.ai_summary} />
        </>
      )}
    </div>
  );
}
