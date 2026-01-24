import React, { useState } from "react";
export default function CarCard({ car }) {
  return (
    <div style={styles.card}>
      <h3 style={styles.title}>
        {car.year} {car.make} {car.model}
      </h3>
      <p><strong>Engine:</strong> {car.engine}</p>
      <p><strong>Fuel:</strong> {car.fuel_type}</p>
      <p><strong>Age:</strong> {car.age} years</p>
      <p style={styles.vin}>{car.vin}</p>
    </div>
  );
}

const styles = {
  card: {
    background: "white",
    borderRadius: "12px",
    padding: "1.5rem",
    boxShadow: "0 10px 20px rgba(0,0,0,0.08)"
  },
  title: {
    marginBottom: "0.5rem"
  },
  vin: {
    marginTop: "1rem",
    fontSize: "0.75rem",
    color: "#777"
  }
};
