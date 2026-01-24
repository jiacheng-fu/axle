export default function CarCard({ car }) {
  return (
    <div className="card">
      <h3>{car.year} {car.make} {car.model}</h3>
      <p>Engine: {car.engine}</p>
      <p>Fuel: {car.fuel_type}</p>
      <p>Age: {car.age} years</p>
    </div>
  );
}
