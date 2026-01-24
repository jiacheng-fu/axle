import React, { useState } from "react";

export default function CarCard({ car }) {
  return (
    <div className="car-card">
      <h3 className="car-title">
        {car.year} {car.make} {car.model}
      </h3>

      <p className="car-sub">
        {car.engine} • {car.fuel_type}
      </p>

      <div style={{display:'flex', gap:8, marginTop:12, alignItems:'center'}}>
        <div className="meta-badge">${car.price_estimate ? car.price_estimate.toLocaleString() : '—'}</div>
        <div className="meta-badge">Reliability: {car.reliability_score ?? '—'}</div>
        <div style={{marginLeft:'auto'}} className="small-muted"><strong>Age:</strong> {car.age ?? '—'} yrs</div>
      </div>

      <div className="vin-tag">VIN {car.vin}</div>
    </div>
  );
}
