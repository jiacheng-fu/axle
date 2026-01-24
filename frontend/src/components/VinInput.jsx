export default function VinInput({ onSubmit }) {
  const [value, setValue] = useState("");

  return (
    <div>
      <textarea
        placeholder="Enter VINs (one per line)"
        onChange={(e) => setValue(e.target.value)}
      />
      <button onClick={() => onSubmit(value.split("\n"))}>
        Compare Cars
      </button>
    </div>
  );
}
